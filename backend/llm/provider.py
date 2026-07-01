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
import os
import time
import traceback
from ..config import settings

# Diagnostic log: one JSONL line per JSON *parse failure* (not per call). Persisted in-repo
# under logs/ so it survives restarts. Override the location with QWEN_DEBUG_LOG.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEBUG_LOG_PATH = os.environ.get(
    "QWEN_DEBUG_LOG", os.path.join(_PROJECT_ROOT, "logs", "qwen_json_failures.jsonl")
)

# Model tiering — assign per agent class via `llm_model` class variable
FAST_MODEL = "qwen-turbo"          # Scout, Trend, Finance, Growth — cheap parallel fan-out
DEEP_MODEL = settings.qwen_model   # Skeptic, Capability, Chair (venture_partner) — set via QWEN_MODEL in .env

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
                _log_parse_failure(self.model, max_tokens, attempt, resp, text, last_error)

        raise ValueError(
            f"Qwen returned invalid JSON after 3 attempts on model {self.model}. "
            f"Last error: {last_error}"
        )


def _call_site() -> str:
    """Best-effort: first stack frame outside this provider module (e.g. the agent)."""
    here = os.path.basename(__file__)
    for frame in reversed(traceback.extract_stack()[:-1]):
        if os.path.basename(frame.filename) != here:
            return f"{os.path.basename(frame.filename)}:{frame.lineno} in {frame.name}"
    return "unknown"


def _usage_dict(resp) -> dict | None:
    """Serialize resp.usage, preserving completion_tokens_details if the SDK exposes it."""
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None
    for attr in ("model_dump", "to_dict", "dict"):
        fn = getattr(usage, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    # Fallback: pull common fields by hand.
    out = {}
    for f in ("prompt_tokens", "completion_tokens", "total_tokens", "completion_tokens_details"):
        if hasattr(usage, f):
            out[f] = getattr(usage, f)
    return out or None


def _log_parse_failure(model, max_tokens, attempt, resp, text, error) -> None:
    """Append one diagnostic JSONL line per failed parse. Never raises (best-effort)."""
    try:
        message = resp.choices[0].message
        reasoning = getattr(message, "reasoning_content", None)
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "call_site": _call_site(),
            "model": model,
            "max_tokens": max_tokens,
            "attempt": attempt,  # 0-indexed retry attempt
            "parse_error": error,
            "content_len": len(text) if text is not None else 0,
            "raw_text": text,
            "reasoning_content_len": len(reasoning) if reasoning else 0,
            "reasoning_content": reasoning if reasoning else None,
            "usage": _usage_dict(resp),
        }
        os.makedirs(os.path.dirname(_DEBUG_LOG_PATH), exist_ok=True)
        with open(_DEBUG_LOG_PATH, "a") as fh:
            fh.write(json.dumps(record, default=str) + "\n")
    except Exception as log_err:  # diagnostics must never break the pipeline
        try:
            with open(_DEBUG_LOG_PATH, "a") as fh:
                fh.write(json.dumps({"log_error": str(log_err)}) + "\n")
        except Exception:
            pass


def _cache_key(model: str, system: str, user: str) -> str:
    # Hash the FULL prompt — truncating (was system[:120]|user[:300]) made
    # different prompts collide. The VP's memory block sits past char 300, so a
    # second run for the same founder returned the first run's cached output,
    # silently defeating the memory loop (Sprint B).
    payload = f"{model}|{system}|{user}"
    return hashlib.md5(payload.encode()).hexdigest()
