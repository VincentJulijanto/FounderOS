from typing import Dict, Any
from .base import BaseAgent
from ..models import UserProfile, AgentOutput


SYSTEM_PROMPT = """
You are the Finance Agent at FounderOS, an AI Venture Studio.

Your mission: Provide realistic financial analysis for each startup opportunity.
Consider the founder's actual budget and time constraints.

For each opportunity, estimate:
- Startup cost (one-time setup)
- Monthly operating cost
- Time to first revenue (months)
- Month 1 / Month 3 / Month 6 revenue projections
- Break-even point
- Financial Feasibility Score (0-10)

Be conservative. Founders are students/young professionals with limited capital.

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "financial_analysis": [
    {
      "opportunity_name": "string",
      "startup_cost_sgd": number,
      "monthly_opex_sgd": number,
      "time_to_first_revenue_months": number,
      "revenue_month_1_sgd": number,
      "revenue_month_3_sgd": number,
      "revenue_month_6_sgd": number,
      "break_even_months": number,
      "profit_margin_pct": number,
      "feasibility_score": 0-10,
      "within_budget": true/false,
      "funding_gap_sgd": number,
      "monetization_model": "string",
      "key_cost_drivers": ["cost 1", "cost 2"],
      "verdict": "FEASIBLE | STRETCH | INFEASIBLE"
    }
  ],
  "financial_summary": "overall financial assessment",
  "top_financial_pick": "most financially attractive opportunity"
}
"""


class FinanceAgent(BaseAgent):
    name = "Finance Agent"
    role = "Financial Feasibility Analysis"

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        opportunities = context.get("opportunities", [])
        profile_text = self._format_profile(profile)

        opp_list = "\n".join(
            f"- {opp['name']}: {opp.get('description', opp.get('tagline', ''))}"
            for opp in opportunities
        ) if opportunities else "Analyse general startup financial feasibility."

        user_message = (
            f"{profile_text}\n\n"
            f"Perform financial analysis for these opportunities:\n{opp_list}\n\n"
            f"The founder's total budget is SGD {profile.budget}. "
            "Be realistic and conservative in projections."
        )

        raw = self._call_claude(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        analysis = data.get("financial_analysis", [])
        top_pick = data.get("top_financial_pick", "")

        feasible = [
            a["opportunity_name"]
            for a in analysis
            if a.get("verdict") == "FEASIBLE"
        ]
        infeasible = [
            f"{a['opportunity_name']} exceeds budget by SGD {a.get('funding_gap_sgd', 0)}"
            for a in analysis
            if a.get("verdict") == "INFEASIBLE"
        ]

        avg_score = (
            sum(a.get("feasibility_score", 0) for a in analysis) / len(analysis)
            if analysis else 0
        )

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("financial_summary", ""),
            score=round(avg_score, 1),
            key_findings=[f"Financially feasible: {', '.join(feasible)}"] if feasible else [],
            concerns=infeasible,
            recommendations=[top_pick] if top_pick else [],
            raw_data=data,
        )
