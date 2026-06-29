"""
QwenProvider — single LLM access point for all FounderOS agents.

Features:
  - OpenAI-compatible SDK against the QwenCloud DashScope endpoint
  - Model tiering: FAST_MODEL for cheap fan-out, DEEP_MODEL for reasoning
  - In-process response cache keyed on (model, prompt hash) — cuts latency on retries
  - JSON-mode retry: feeds parse error back to Qwen for up to 3 attempts
  - Falls back to mock mode when QWEN_API_KEY is not configured
"""

import json
import hashlib
from ..config import settings

# Model tiering — assign per agent class via `llm_model` class variable
FAST_MODEL = "qwen-turbo"   # Scout, Trend, Finance, Growth — cheap parallel fan-out
DEEP_MODEL = "qwen-plus"    # Skeptic, Venture Partner, Debate Engine — reasoning-heavy

_cache: dict[str, str] = {}  # in-process cache; swap for Redis in production


class QwenProvider:
    """
    Thin wrapper around the OpenAI-compatible Qwen SDK.
    Constructed once per agent instance and reused across calls.
    """

    def __init__(self, model: str = DEEP_MODEL):
        self.model = model
        self.mock = settings.use_mock_llm or not settings.qwen_api_key
        if not self.mock:
            from openai import OpenAI  # lazy — only imported when a real key exists
            self._client = OpenAI(
                api_key=settings.qwen_api_key,
                base_url=settings.qwen_base_url,
            )

    def chat(self, system: str, user: str, max_tokens: int = 2000) -> str:
        """
        Send a chat request to Qwen and return the raw JSON string.
        Raises RuntimeError if called in mock mode (callers check .mock first).
        Hits cache before making a network call.
        """
        if self.mock:
            raise RuntimeError("QwenProvider.chat() called in mock mode — check self.mock before calling.")

        key = _cache_key(self.model, system, user)
        if key in _cache:
            return _cache[key]

        result = self._call_with_retry(system, user, max_tokens)
        _cache[key] = result
        return result

    def _call_with_retry(self, system: str, user: str, max_tokens: int) -> str:
        """Call Qwen up to 3 times, feeding JSON parse errors back on each retry."""
        last_error = ""
        for attempt in range(3):
            user_msg = user if attempt == 0 else (
                f"{user}\n\n"
                f"Your previous response had a JSON parse error: {last_error}\n"
                "Return valid JSON only — no preamble, no markdown fences."
            )
            resp = self._client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
            )
            text = resp.choices[0].message.content
            try:
                json.loads(text)  # validate before caching
                return text
            except json.JSONDecodeError as e:
                last_error = str(e)

        raise ValueError(
            f"Qwen returned invalid JSON after 3 attempts on model {self.model}. "
            f"Last error: {last_error}"
        )


def _cache_key(model: str, system: str, user: str) -> str:
    # Hash the FULL prompt — truncating (was system[:120]|user[:300]) made
    # different prompts collide. The VP's memory block sits past char 300, so a
    # second run for the same founder returned the first run's cached output,
    # silently defeating the memory loop (Sprint B).
    payload = f"{model}|{system}|{user}"
    return hashlib.md5(payload.encode()).hexdigest()
