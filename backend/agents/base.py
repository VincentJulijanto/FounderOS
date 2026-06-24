import json
import re
import anthropic
from typing import Dict, Any
from ..config import settings
from ..models import UserProfile, AgentOutput


class BaseAgent:
    """
    Base class for all FounderOS agents.
    Provides shared Claude API access and JSON parsing utilities.
    """

    name: str = "Base Agent"
    role: str = "Base"

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    # ──────────────────────────────────────────
    # Core LLM Call
    # ──────────────────────────────────────────

    def _call_claude(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 2000,
    ) -> str:
        """Call Claude and return the raw text response."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    # ──────────────────────────────────────────
    # JSON Parsing
    # ──────────────────────────────────────────

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from a Claude response.
        Handles raw JSON and ```json ... ``` code blocks.
        """
        # Strip markdown fences if present
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
