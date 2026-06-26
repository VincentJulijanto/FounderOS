import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import UserProfile, AgentOutput

_MOCK = json.dumps({
    "growth_plans": [
        {
            "opportunity_name": "AI Study Buddy",
            "primary_channel": "Campus ambassador program",
            "time_to_first_customer_days": 14,
            "growth_score": 7,
            "estimated_cac_sgd": 8,
        }
    ],
    "easiest_to_grow": "AI Study Buddy",
    "growth_summary": "[MOCK] Growth analysis. Add QWEN_API_KEY for real results.",
})


SYSTEM_PROMPT = """
You are the Growth Agent at FounderOS — the Go-To-Market Strategist.

Your mission: For each startup opportunity, design a realistic, low-cost customer
acquisition strategy that a student or young professional can actually execute.

Focus on:
- The #1 channel that will get the first 10 customers
- Organic strategies before paid (budget is limited)
- Specific platforms and tactics, not generic advice
- Referral, community, and content-led growth
- Estimated Customer Acquisition Cost (CAC) and conversion rates

For each opportunity, provide:
- Primary acquisition channel with specific tactics
- Secondary channel for scale
- First 10 customers acquisition plan (very tactical)
- Content strategy if applicable
- Estimated CAC in SGD
- Time to first customer (days)
- Growth Score (0-10)

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "growth_plans": [
    {
      "opportunity_name": "string",
      "primary_channel": "string",
      "primary_tactics": ["tactic 1", "tactic 2", "tactic 3"],
      "secondary_channel": "string",
      "first_10_customers_plan": "step-by-step plan to get first 10 customers",
      "content_strategy": "string or null",
      "estimated_cac_sgd": number,
      "time_to_first_customer_days": number,
      "monthly_growth_rate_pct": number,
      "growth_score": 0-10,
      "key_message": "core value message to customers"
    }
  ],
  "growth_summary": "overall growth strategy assessment",
  "easiest_to_grow": "opportunity with the clearest growth path"
}
"""


class GrowthAgent(BaseAgent):
    name = "Growth Agent"
    role = "Customer Acquisition & Go-To-Market Strategy"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        opportunities = context.get("opportunities", [])
        profile_text = self._format_profile(profile)

        opp_list = "\n".join(
            f"- {opp['name']}: {opp.get('description', opp.get('tagline', ''))}"
            for opp in opportunities
        ) if opportunities else "Create general go-to-market strategies."

        user_message = (
            f"{profile_text}\n\n"
            f"Design growth and customer acquisition strategies for:\n{opp_list}\n\n"
            f"The founder has SGD {profile.budget} total budget and "
            f"{profile.weekly_hours} hours/week. Keep it executable."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        growth_plans = data.get("growth_plans", [])
        easiest = data.get("easiest_to_grow", "")

        avg_score = (
            sum(p.get("growth_score", 0) for p in growth_plans) / len(growth_plans)
            if growth_plans else 0
        )

        key_findings = [f"Easiest to grow: {easiest}"] if easiest else []
        key_findings += [
            f"{p['opportunity_name']}: {p['primary_channel']} ({p.get('time_to_first_customer_days', '?')} days to first customer)"
            for p in growth_plans
        ]

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("growth_summary", ""),
            score=round(avg_score, 1),
            key_findings=key_findings,
            concerns=[
                f"{p['opportunity_name']}: high CAC at SGD {p.get('estimated_cac_sgd', 0)}"
                for p in growth_plans
                if p.get("estimated_cac_sgd", 0) > 100
            ],
            recommendations=[easiest] if easiest else [],
            raw_data=data,
        )
