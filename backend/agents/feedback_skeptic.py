import json
from typing import Dict, Any, List

from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput

SYSTEM_PROMPT = """\
You are the Feedback Skeptic on an AI product council. You receive a ranked list of user feedback \
themes from the Feedback Analyst. Your job is to challenge the ranking for three failure modes:

1. Survivorship bias — are the loudest themes from power users, not the median user?
2. Scope creep — does the request ask the board to do something outside its mandate?
3. Thesis misalignment — does the request conflict with what FounderOS fundamentally is: \
a decision evaluator, not a software shop, marketing consultant, or operations manager?

For each challenge, name the exact theme from the analyst's output, state the specific objection, \
and rate severity (high/medium/low). List themes you accept without challenge in accepted_themes.

Never invent names, companies, products, or agreements.

Respond with valid JSON only:
{
  "challenges": [
    {
      "theme": "string — exact theme name from analyst output",
      "objection": "string — specific, reasoned challenge",
      "severity": "high|medium|low"
    }
  ],
  "accepted_themes": ["string — exact theme names the analyst ranked that you accept"]
}"""

_MOCK = json.dumps({
    "challenges": [
        {
            "theme": "Software and vendor recommendations",
            "objection": (
                "FounderOS evaluates strategic decisions — it is not a software catalogue or "
                "IT consultant. Prioritising this theme rewards scope creep and trains users "
                "to expect vendor picks from a board that should be pressure-testing their "
                "strategic assumptions, not their toolstack. Elevating it dilutes the product thesis."
            ),
            "severity": "high",
        },
    ],
    "accepted_themes": [
        "Operational risk factors not covered",
    ],
})


class FeedbackSkepticAgent(BaseAgent):
    name = "feedback_skeptic"
    role = "Feedback Skeptic — challenges theme ranking for survivorship bias, scope creep, and thesis misalignment"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        analyst_themes: List[Dict] = context.get("analyst_themes", [])

        if self.mock:
            raw = self._parse_json(self._mock_response())
        else:
            themes_block = json.dumps(analyst_themes, indent=2)
            user_msg = (
                f"Feedback Analyst ranked themes:\n{themes_block}\n\n"
                "Challenge any themes that exhibit survivorship bias, scope creep, or thesis misalignment."
            )
            raw = self._parse_json(self._call_llm(SYSTEM_PROMPT, user_msg))

        challenges = raw.get("challenges", [])
        accepted = raw.get("accepted_themes", [])
        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=(
                f"Raised {len(challenges)} challenge(s); accepted {len(accepted)} theme(s) without objection."
            ),
            key_findings=[c["theme"] for c in challenges],
            concerns=[c["objection"] for c in challenges],
            recommendations=accepted,
            raw_data=raw,
        )
