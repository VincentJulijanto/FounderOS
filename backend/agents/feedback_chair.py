import json
from typing import Dict, Any, List

from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput

SYSTEM_PROMPT = """\
You are the Product Chair on an AI product council. You receive:
- The Feedback Analyst's ranked themes
- The Feedback Skeptic's specific challenges

For each theme the Skeptic challenged, decide one of:
- "accepted": the Skeptic is right — remove this theme
- "reframed": the Skeptic has a point but the underlying user need is real — reformulate \
the theme to stay thesis-aligned (do NOT invent a theme unrelated to the feedback)
- "overridden": the Skeptic's challenge is wrong — keep the original theme with rationale

Produce final_themes in priority order, the overrides record for auditability, and a \
ranked_brief in plain operator language (2–4 bullet points).

Never invent names, companies, products, or agreements.

Respond with valid JSON only:
{
  "final_themes": [
    {
      "theme": "string",
      "frequency": int,
      "representative_quotes": ["string"],
      "priority": "high|medium|low",
      "thesis_aligned": bool
    }
  ],
  "overrides": [
    {
      "theme": "string — original theme name from analyst",
      "decision": "accepted|reframed|overridden",
      "rationale": "string — why"
    }
  ],
  "ranked_brief": "string — 2–4 bullet points in plain operator language"
}"""

_MOCK = json.dumps({
    "final_themes": [
        {
            "theme": "Operational risk factors not covered",
            "frequency": 2,
            "representative_quotes": [
                "The board didn't factor in port congestion risk at Cai Mep",
                "Customs brokerage should have been flagged as a blocker, not just a gap",
            ],
            "priority": "high",
            "thesis_aligned": True,
        },
        {
            "theme": "Board reasoning transparency — why certain risks were not foregrounded",
            "frequency": 1,
            "representative_quotes": [
                "Never mentioned which TMS or visibility platform we should be using",
            ],
            "priority": "low",
            "thesis_aligned": True,
        },
    ],
    "overrides": [
        {
            "theme": "Software and vendor recommendations",
            "decision": "reframed",
            "rationale": (
                "The Skeptic is right that vendor picks are out of scope. However, the user's "
                "underlying frustration is real: the board did not explain why it stayed silent "
                "on implementation specifics. Reframed as a reasoning-transparency theme — a "
                "valid prompt to improve how the board explains the boundaries of its mandate "
                "without users feeling the memo is incomplete."
            ),
        },
    ],
    "ranked_brief": (
        "• Priority 1 (high): Improve coverage of operational risk factors in cross-border "
        "decisions — specifically transit-time variability (port congestion) and customs "
        "brokerage lead times. These are within the board's mandate and the gaps are material "
        "to the decisions being evaluated.\n"
        "• Priority 2 (low): Improve reasoning transparency so users understand why certain "
        "tactical specifics (vendor selection, toolstack) are outside the board's scope. "
        "A brief mandate note in the memo would resolve recurring friction without the board "
        "overstepping into IT consulting."
    ),
})


class FeedbackChairAgent(BaseAgent):
    name = "feedback_chair"
    role = "Product Chair — synthesizes analyst themes and skeptic challenges into a ranked brief"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        analyst_themes: List[Dict] = context.get("analyst_themes", [])
        skeptic_challenges: List[Dict] = context.get("skeptic_challenges", [])
        accepted_themes: List[str] = context.get("accepted_themes", [])

        if self.mock:
            raw = self._parse_json(self._mock_response())
        else:
            user_msg = (
                f"Analyst themes:\n{json.dumps(analyst_themes, indent=2)}\n\n"
                f"Skeptic challenges:\n{json.dumps(skeptic_challenges, indent=2)}\n\n"
                f"Skeptic accepted (no challenge): {accepted_themes}\n\n"
                "Produce the final ranked brief, resolving each challenge."
            )
            raw = self._parse_json(self._call_llm(SYSTEM_PROMPT, user_msg))

        final_themes = raw.get("final_themes", [])
        overrides = raw.get("overrides", [])
        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=raw.get("ranked_brief", ""),
            key_findings=[t["theme"] for t in final_themes],
            concerns=[o["rationale"] for o in overrides if o.get("decision") == "accepted"],
            recommendations=[o["rationale"] for o in overrides if o.get("decision") != "accepted"],
            raw_data=raw,
        )
