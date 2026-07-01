import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput
from ..mcp.client import mcp_client, run_sync

_MOCK = json.dumps({
    "options": [
        "Full subsidiary in the new market",
        "Asset-light partnership with a local operator",
        "Hold and deepen the current market before expanding",
    ],
    "framing": (
        "[MOCK] Scout framing. Add QWEN_API_KEY for real results. The decision reduces to "
        "how much fixed commitment to take on versus preserving optionality."
    ),
    "recommended_frame": "Weigh speed-to-market against capital-at-risk and reversibility.",
})


SYSTEM_PROMPT = """
You are the Opportunity Scout on an AI board of directors advising an EXISTING company.

Your job is NOT to invent new business ideas. Your job is to frame the DECISION on the
table: lay out the realistic OPTIONS (alternative approaches to this one decision) so the
board can evaluate them. If the operator already listed options, sharpen and complete them;
if they left options empty, generate 2–4 credible alternatives (always include the
"do nothing / hold" option where relevant).

Ground your framing in the company's stage, sector, and the live market data provided.

IMPORTANT: You MUST respond with valid JSON only — no preamble, no markdown, no explanation.

Output format:
{
  "options": ["option 1", "option 2", "option 3"],
  "framing": "2-3 sentences framing what this decision really turns on",
  "recommended_frame": "the single lens the board should judge these options through"
}
"""


class OpportunityScoutAgent(BaseAgent):
    name = "scout"
    role = "Opportunity Scout — frames the options on the table"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        # ── MCP: ground the framing in live market data for this company's sector.
        # Mock-safe — falls back to deterministic fixtures with no credentials.
        probe = profile.sector or decision.question
        crunchbase = run_sync(mcp_client.search_crunchbase(probe))
        news = run_sync(mcp_client.fetch_news(probe))
        mcp_sources = _dedupe(crunchbase.get("sources", []) + news.get("sources", []))
        market_data_block = _format_market_data(crunchbase, news)

        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            "## Live Market Data\n"
            f"{market_data_block}\n\n"
            "Frame the options for this decision. If options are already listed, refine and "
            "complete them; otherwise generate 2–4 credible alternatives including a hold option."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        # Preserve the operator's options when they supplied them (Scout refines,
        # it does not replace the operator's stated alternatives). Only fall back
        # to the framed set when the operator left options empty.
        options = (decision.options or []) or data.get("options") or []

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("framing", ""),
            key_findings=[data.get("recommended_frame", "")] if data.get("recommended_frame") else [],
            recommendations=options,
            concerns=[],
            raw_data={
                "options": options,
                "framing": data.get("framing", ""),
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
