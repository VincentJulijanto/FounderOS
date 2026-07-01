import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput

_MOCK = json.dumps({
    "execution_read": (
        "[MOCK] Growth analysis. Add QWEN_API_KEY for real results. The company can execute "
        "the chosen option but go-to-market depends on channels it has not yet proven."
    ),
    "go_to_market": "Lead with the two anchor customers, then expand via referrals.",
    "growth_score": 7.0,
    "levers": ["Anchor-customer land-and-expand", "Local partnership for distribution"],
    "execution_risks": ["Unproven channel in the new segment", "Sales cycle longer than planned"],
    "verdict": "EXECUTABLE",
})


SYSTEM_PROMPT = """
You are the Growth Agent on an AI board advising an EXISTING company on ONE decision.

Judge how the company would EXECUTE and GO TO MARKET on the chosen option: the channels,
the motion, and how quickly it can show traction. Use what you know about the company's
stage and model. Be specific about the levers and the execution risks.

Score execution readiness 0-10.

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "execution_read": "how well the company can execute this decision",
  "go_to_market": "the concrete motion to reach customers on the chosen option",
  "growth_score": 0-10,
  "levers": ["lever 1", "lever 2"],
  "execution_risks": ["risk 1", "risk 2"],
  "verdict": "EXECUTABLE | STRETCH | UNLIKELY"
}
"""


class GrowthAgent(BaseAgent):
    name = "growth"
    role = "Growth Agent — execution & go-to-market on the decision"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            "Assess how this company would execute and go to market on this decision. "
            "Be concrete about channels, levers, and execution risk."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("execution_read", ""),
            score=data.get("growth_score"),
            key_findings=[data.get("go_to_market", "")] + data.get("levers", []),
            concerns=data.get("execution_risks", []),
            recommendations=[data.get("verdict", "")] if data.get("verdict") else [],
            raw_data=data,
        )
