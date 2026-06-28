import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import UserProfile, AgentOutput
from ..mcp.client import mcp_client, run_sync

_MOCK = json.dumps({
    "opportunities": [
        {
            "name": "AI Study Buddy",
            "tagline": "Your AI tutor, always available",
            "description": "Personalised AI tutoring app for university students",
            "skills_required": ["Python", "web development"],
            "budget_required": "SGD 200",
            "time_to_first_revenue": "3 weeks",
            "revenue_model": "Monthly subscription",
            "competitive_landscape": "Medium",
        }
    ],
    "top_pick": "AI Study Buddy",
    "scout_rationale": "[MOCK] Scout analysis. Add QWEN_API_KEY for real results.",
})


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

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        profile_text = self._format_profile(profile)

        # ── MCP (Phase 6): ground the scout in live market data before reasoning.
        # The founder's primary interest stands in for the sector to probe; pre-scout
        # there is no concrete startup name yet. Mock-safe — falls back to fixtures.
        industry = profile.interests[0] if profile.interests else "technology startups"
        crunchbase = run_sync(mcp_client.search_crunchbase(industry))
        news = run_sync(mcp_client.fetch_news(industry))
        mcp_sources = _dedupe(crunchbase.get("sources", []) + news.get("sources", []))
        market_data_block = _format_market_data(crunchbase, news)

        user_message = (
            f"{profile_text}\n\n"
            "## Live Market Data\n"
            f"{market_data_block}\n\n"
            "Scout 5 startup opportunities for this founder. "
            "Prioritize opportunities that play to their strengths and can be launched "
            "within their budget and weekly hours."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
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
                "mcp_sources": mcp_sources,
            },
        )


def _dedupe(items: list[str]) -> list[str]:
    """Order-preserving de-duplication."""
    return list(dict.fromkeys(items))


def _format_market_data(crunchbase: Dict[str, Any], news: Dict[str, Any]) -> str:
    """Render MCP results into a compact prompt block."""
    lines = ["Comparable companies (Crunchbase):"]
    for c in crunchbase.get("results", []):
        lines.append(f"- {c.get('name')} — {c.get('funding_total')} ({c.get('last_round')}): {c.get('description')}")
    lines.append("Recent news:")
    for a in news.get("articles", []):
        lines.append(f"- {a.get('headline')} ({a.get('source')}): {a.get('summary')}")
    return "\n".join(lines)
