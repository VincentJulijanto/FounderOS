import json
import re
from typing import Dict, Any
from ..config import settings
from ..models import UserProfile, AgentOutput
from ..llm.provider import QwenProvider, FAST_MODEL


class BaseAgent:
    """
    Base class for all FounderOS agents.

    Subclasses set `llm_model` to control model tiering:
      - FAST_MODEL (qwen-turbo)  — Scout, Trend, Finance, Growth
      - DEEP_MODEL (qwen-plus)   — Skeptic, Venture Partner
    """

    name: str = "Base Agent"
    role: str = "Base"
    llm_model: str = FAST_MODEL  # override in subclass for reasoning-heavy agents
    max_tokens: int = 2000       # override for agents whose JSON output is large
                                 # (Skeptic, VP) — too low truncates JSON in live mode

    def __init__(self):
        self.mock = settings.use_mock_llm or not settings.qwen_api_key
        self.provider = QwenProvider(model=self.llm_model)

    # ──────────────────────────────────────────
    # Core LLM Call
    # ──────────────────────────────────────────

    def _call_llm(self, system: str, user: str, max_tokens: int | None = None) -> str:
        """Return mock fixture or live Qwen response depending on config.

        max_tokens defaults to the agent's class-level `max_tokens` so each agent
        controls its own ceiling; pass an explicit value to override per call.
        """
        if self.mock:
            return self._mock_response()
        return self.provider.chat(system, user, max_tokens or self.max_tokens)

    def _mock_response(self) -> str:
        """Override in each subclass with a realistic fixture for mock mode."""
        return json.dumps({"mock": True, "agent": self.name})

    # ──────────────────────────────────────────
    # JSON Parsing
    # ──────────────────────────────────────────

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from a Qwen response, handling markdown fences."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            text = fence_match.group(1)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            raise ValueError(
                f"[{self.name}] Failed to parse JSON response.\n"
                f"Error: {e}\nRaw text (first 400 chars):\n{text[:400]}"
            )

    # ──────────────────────────────────────────
    # Profile Formatter (shared by all agents)
    # ──────────────────────────────────────────

    def _format_profile(self, profile: UserProfile) -> str:
        return (
            f"Founder Profile:\n"
            f"- Name: {profile.name}\n"
            f"- Background: {profile.background}\n"
            f"- Skills: {', '.join(profile.skills)}\n"
            f"- Budget: SGD {profile.budget}\n"
            f"- Available Time: {profile.weekly_hours} hours/week\n"
            f"- Interests: {', '.join(profile.interests)}\n"
            f"- Goals: {profile.goals}\n"
        )

    # ──────────────────────────────────────────
    # Override in subclasses
    # ──────────────────────────────────────────

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        raise NotImplementedError("Each agent must implement analyze()")
