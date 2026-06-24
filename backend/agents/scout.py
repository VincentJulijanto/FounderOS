from typing import Dict, Any
from .base import BaseAgent
from ..models import UserProfile, AgentOutput


SYSTEM_PROMPT = """
You are the Opportunity Scout at FounderOS, an AI Venture Studio.

Your mission: Given a founder's profile, discover 5 high-potential startup opportunities
they could realistically launch.

Focus on:
- Underserved market gaps that match their skills
- Opportunities executable within their budget and time constraints
- Ideas appropriate for their local context (assume Singapore unless stated)
- Both digital (SaaS, content, freelance) and service-based opportunities

IMPORTANT: You MUST respond with valid JSON only — no preamble, no markdown, no explanation.

Output format:
{
  "opportunities": [
    {
      "name": "string",
      "tagline": "one line pitch",
      "description": "2-3 sentence description",
      "target_market": "who buys this",
      "why_now": "market timing rationale",
      "skill_match": "how founder's skills apply",
      "estimated_revenue": "SGD X/month within Y months"
    }
  ],
  "scout_rationale": "brief explanation of your scouting approach",
  "top_pick": "name of the strongest opportunity and why"
}
"""


class OpportunityScoutAgent(BaseAgent):
    name = "Opportunity Scout"
    role = "Market Opportunity Discovery"

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        profile_text = self._format_profile(profile)

        user_message = (
            f"{profile_text}\n\n"
            "Scout 5 startup opportunities for this founder. "
            "Prioritize opportunities that play to their strengths and can be launched "
            "within their budget and weekly hours."
        )

        raw = self._call_claude(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        opportunities = data.get("opportunities", [])
        top_pick = data.get("top_pick", "")

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("scout_rationale", ""),
            recommendations=[opp["name"] for opp in opportunities],
            key_findings=[
                f"{opp['name']}: {opp['tagline']}" for opp in opportunities
            ],
            concerns=[],
            raw_data={
                "opportunities": opportunities,
                "top_pick": top_pick,
            },
        )
