import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput
from ..mcp.client import mcp_client, run_sync

_MOCK = json.dumps({
    "market_read": (
        "[MOCK] Trend analysis. Add QWEN_API_KEY for real results. Demand signals for this "
        "decision are moderately favourable but timing risk is real."
    ),
    "demand_score": 7.0,
    "signals": ["Rising demand in adjacent markets", "Incumbents moving slowly"],
    "timing_risks": ["Macro softness could delay payback"],
    "verdict": "MODERATE",
})


SYSTEM_PROMPT = """
You are the Trend Analyst on an AI board advising an EXISTING company on ONE decision.

Read the market and demand signals that bear on THIS decision — not generic industry
commentary. Use the live signals provided. Judge whether the timing and demand support the
options on the table.

Score demand 0-10 (10 = strong tailwind) and be explicit about timing risk.

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "market_read": "what the market signals say about this decision",
  "demand_score": 0-10,
  "signals": ["signal 1", "signal 2"],
  "timing_risks": ["risk 1", "risk 2"],
  "verdict": "STRONG | MODERATE | WEAK"
}
"""


class TrendAnalystAgent(BaseAgent):
    name = "trend"
    role = "Trend Analyst — market & demand signals for the decision"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        # ── MCP: pull current web signals for the company's sector + decision.
        query = f"{profile.sector} {decision.question} 2026"
        web = run_sync(mcp_client.search_web(query))
        mcp_sources = list(dict.fromkeys(web.get("sources", [])))
        signals_block = "\n".join(
            f"- {r.get('title')}: {r.get('snippet')}" for r in web.get("results", [])
        ) or "No live signals available."

        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            "## Current Signals\n"
            f"{signals_block}\n\n"
            "Assess whether market demand and timing support this decision."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)
        data["mcp_sources"] = mcp_sources

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("market_read", ""),
            score=data.get("demand_score"),
            key_findings=data.get("signals", []),
            concerns=data.get("timing_risks", []),
            recommendations=[data.get("verdict", "")] if data.get("verdict") else [],
            raw_data=data,
        )
