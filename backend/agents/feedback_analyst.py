import json
from typing import Dict, Any, List

from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput

SYSTEM_PROMPT = """\
You are the Feedback Analyst on an AI product council. You receive a list of user-submitted \
feedback on what was missing from recent board decisions. Your job is to cluster the feedback \
into recurring themes, count frequency, and rank by priority.

For each theme, assess whether it is "thesis_aligned" — does it ask the board to do something \
within its mandate (evaluate decisions, surface risks, assess options)? A request for the board \
to recommend specific software products or vendors is NOT thesis-aligned (that is IT consulting, \
not board work).

Never invent names, companies, products, or agreements that are not present in the feedback \
you receive.

Respond with valid JSON only:
{
  "themes": [
    {
      "theme": "string — clear theme label",
      "frequency": int,
      "representative_quotes": ["up to 2 direct quotes from feedback"],
      "priority": "high|medium|low",
      "thesis_aligned": bool
    }
  ],
  "baseline_summary": "string — flat one-paragraph summary a single agent would produce (no critical filter)"
}"""

_MOCK = json.dumps({
    "themes": [
        {
            "theme": "Operational risk factors not covered",
            "frequency": 2,
            "representative_quotes": [
                "The board didn't factor in port congestion risk at Cai Mep",
                "The customs brokerage piece was left as a 'missing input' — should have been flagged as a blocker",
            ],
            "priority": "high",
            "thesis_aligned": True,
        },
        {
            "theme": "Software and vendor recommendations",
            "frequency": 1,
            "representative_quotes": [
                "Never mentioned which TMS or visibility platform we should be using",
            ],
            "priority": "medium",
            "thesis_aligned": False,
        },
    ],
    "baseline_summary": (
        "Users want more coverage of operational risk factors — specifically port congestion "
        "and customs brokerage costs in cross-border logistics decisions. One user also asked "
        "for software and vendor recommendations to support the asset-light strategy."
    ),
})


class FeedbackAnalystAgent(BaseAgent):
    name = "feedback_analyst"
    role = "Feedback Analyst — clusters user-reported gaps into ranked themes"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        feedback_texts: List[str] = context.get("feedback_texts", [])

        if self.mock:
            raw = self._parse_json(self._mock_response())
        else:
            numbered = "\n".join(
                f"{i + 1}. {t.strip()}" for i, t in enumerate(feedback_texts)
            ) or "(no feedback notes found)"
            user_msg = f"User feedback submissions:\n{numbered}"
            raw = self._parse_json(self._call_llm(SYSTEM_PROMPT, user_msg))

        themes = raw.get("themes", [])
        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=raw.get("baseline_summary", ""),
            key_findings=[t["theme"] for t in themes],
            concerns=[t["theme"] for t in themes if not t.get("thesis_aligned", True)],
            recommendations=[],
            raw_data=raw,
        )
