import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import UserProfile, AgentOutput

_MOCK = json.dumps({
    "market_analysis": [
        {
            "opportunity_name": "AI Study Buddy",
            "market_size": "SGD 50M Singapore edtech",
            "growth_rate": "35% YoY",
            "demand_signals": ["Rising AI tool adoption", "Student cost pressures"],
            "market_attractiveness_score": 8,
            "verdict": "STRONG",
        }
    ],
    "top_market_pick": "AI Study Buddy",
    "trending_now": "[MOCK] Trend analysis. Add QWEN_API_KEY for real results.",
})


SYSTEM_PROMPT = """
You are the Trend Analyst at FounderOS, an AI Venture Studio.

Your mission: Evaluate market attractiveness for each startup opportunity identified
by the Scout Agent. You analyse demand signals, industry growth, competition, and timing.

Score each opportunity from 0-10 on:
- Market demand (how much people want/need this)
- Industry growth (is this market growing?)
- Competition level (lower competition = higher score)
- Timing (is now the right moment?)
- Compute a weighted Market Attractiveness Score (average of above)

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "market_analysis": [
    {
      "opportunity_name": "string",
      "demand_score": 0-10,
      "growth_score": 0-10,
      "competition_score": 0-10,
      "timing_score": 0-10,
      "market_attractiveness_score": 0-10,
      "trend_signals": ["signal 1", "signal 2"],
      "market_size": "estimated TAM/SAM",
      "verdict": "STRONG | MODERATE | WEAK"
    }
  ],
  "trending_now": "what macro trends support these opportunities",
  "top_market_pick": "opportunity with strongest market position"
}
"""


class TrendAnalystAgent(BaseAgent):
    name = "Trend Analyst"
    role = "Market Trend & Demand Evaluation"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        opportunities = context.get("opportunities", [])
        profile_text = self._format_profile(profile)

        opp_list = "\n".join(
            f"- {opp['name']}: {opp.get('tagline', opp.get('description', ''))}"
            for opp in opportunities
        ) if opportunities else "No opportunities provided — generate general analysis."

        user_message = (
            f"{profile_text}\n\n"
            f"Evaluate market attractiveness for these opportunities:\n{opp_list}\n\n"
            "Provide detailed trend analysis and scores for each."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        market_analysis = data.get("market_analysis", [])
        top_pick = data.get("top_market_pick", "")

        strong_markets = [
            m["opportunity_name"]
            for m in market_analysis
            if m.get("verdict") == "STRONG"
        ]

        weak_markets = [
            f"{m['opportunity_name']} (weak market)"
            for m in market_analysis
            if m.get("verdict") == "WEAK"
        ]

        avg_score = (
            sum(m.get("market_attractiveness_score", 0) for m in market_analysis)
            / len(market_analysis)
            if market_analysis else 0
        )

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("trending_now", ""),
            score=round(avg_score, 1),
            key_findings=[f"Top market pick: {top_pick}"] + strong_markets,
            concerns=weak_markets,
            recommendations=[top_pick] if top_pick else [],
            raw_data=data,
        )
