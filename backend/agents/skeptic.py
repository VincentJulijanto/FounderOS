import json
from typing import Dict, Any
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import UserProfile, AgentOutput

_MOCK = json.dumps({
    "risk_reports": [
        {
            "opportunity_name": "AI Study Buddy",
            "failure_risks": [
                {"risk": "API cost scaling", "probability": "Medium", "mitigation": "Implement per-user limits"},
                {"risk": "Student churn after exam season", "probability": "Medium", "mitigation": "Year-round content"},
            ],
            "risk_score": 4,
            "verdict": "PROCEED_WITH_CAUTION",
        }
    ],
    "least_risky": "AI Study Buddy",
    "overall_concern": "[MOCK] Skeptic analysis. Add QWEN_API_KEY for real results.",
})


SYSTEM_PROMPT = """
You are the Skeptic Agent at FounderOS — the Devil's Advocate.

Your mission: Challenge every assumption. Identify the real risks, overlooked weaknesses,
and most likely failure modes for each startup opportunity.

You are NOT pessimistic for its own sake. You are rigorous. Your goal is to stress-test
ideas so only the strongest survive. A good skeptic strengthens good ideas.

For each opportunity, identify:
- The single most dangerous assumption being made
- Top 3 failure risks (with probability estimate: High / Medium / Low)
- Competitive threats the Scout may have underestimated
- Execution risks specific to this founder's constraints
- Whether the financial projections are realistic
- A Risk Score (0-10, where 10 = very risky)

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "risk_reports": [
    {
      "opportunity_name": "string",
      "critical_assumption": "the biggest assumption that could be wrong",
      "failure_risks": [
        {"risk": "string", "probability": "High|Medium|Low", "mitigation": "string"}
      ],
      "competitive_threats": ["threat 1", "threat 2"],
      "execution_risks": ["risk specific to this founder"],
      "financial_reality_check": "honest assessment of projections",
      "risk_score": 0-10,
      "verdict": "PROCEED | PROCEED_WITH_CAUTION | AVOID"
    }
  ],
  "overall_concern": "the single biggest concern across all opportunities",
  "least_risky": "opportunity with the best risk profile"
}
"""


class SkepticAgent(BaseAgent):
    name = "Skeptic Agent"
    role = "Risk Analysis & Devil's Advocate"
    llm_model = DEEP_MODEL  # needs careful reasoning to challenge assumptions
    max_tokens = 6000       # per-opportunity risk JSON over 5 opps truncated at 2000 in live mode (Sprint B)

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        opportunities = context.get("opportunities", [])
        financial_data = context.get("financial_analysis", [])
        market_data = context.get("market_analysis", [])

        profile_text = self._format_profile(profile)

        opp_list = "\n".join(
            f"- {opp['name']}: {opp.get('description', opp.get('tagline', ''))}"
            for opp in opportunities
        ) if opportunities else "Challenge general startup assumptions."

        # Provide financial context for reality checking
        fin_context = ""
        if financial_data:
            fin_context = "\nFinancial projections to reality-check:\n" + "\n".join(
                f"- {a['opportunity_name']}: SGD {a.get('revenue_month_3_sgd', 'N/A')}/month by month 3"
                for a in financial_data
            )

        user_message = (
            f"{profile_text}\n\n"
            f"Challenge these opportunities aggressively:\n{opp_list}"
            f"{fin_context}\n\n"
            "Be specific about risks. Don't hold back."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        risk_reports = data.get("risk_reports", [])
        least_risky = data.get("least_risky", "")

        avoid_list = [
            r["opportunity_name"]
            for r in risk_reports
            if r.get("verdict") == "AVOID"
        ]

        high_risks = []
        for report in risk_reports:
            for risk in report.get("failure_risks", []):
                if risk.get("probability") == "High":
                    high_risks.append(
                        f"{report['opportunity_name']}: {risk['risk']}"
                    )

        avg_risk_score = (
            sum(r.get("risk_score", 5) for r in risk_reports) / len(risk_reports)
            if risk_reports else 5
        )

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("overall_concern", ""),
            score=round(10 - avg_risk_score, 1),  # invert: high score = low risk
            key_findings=[f"Least risky: {least_risky}"] if least_risky else [],
            concerns=high_risks + [f"AVOID: {name}" for name in avoid_list],
            recommendations=[least_risky] if least_risky else [],
            raw_data=data,
        )
