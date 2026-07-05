import json
from typing import Dict, Any
from .base import BaseAgent
from ..models import CompanyProfile, AgentOutput
from ..mcp.client import mcp_client, run_sync

_MOCK = json.dumps({
    "financial_view": (
        "The decision is affordable within the stated budget but compresses "
        "margin for 2-3 quarters before payback."
    ),
    "feasibility_score": 6.5,
    "payback_view": "Break-even around month 9-12 on base-case assumptions.",
    "budget_fit": "Within the stated budget, with limited buffer.",
    "financial_risks": ["Margin compression during ramp", "FX / cost overrun exposure"],
    "verdict": "FEASIBLE",
})


SYSTEM_PROMPT = """
You are the Finance Agent on an AI board advising an EXISTING company on ONE decision.

Model this decision against the COMPANY'S economics — its revenue band, margin, cash
position, and the budget/timeline constraints given. This is not a personal budget: judge
the P&L and cash impact of the options on the table, payback, and whether the company can
afford the downside.

Be conservative. Surface the funding/margin risk honestly.

Never invent names, companies, products, or agreements the operator did not provide — refer to unnamed entities exactly as the operator did (e.g. "the third shipper").

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "financial_view": "plain-language read of the money impact of this decision",
  "feasibility_score": 0-10,
  "payback_view": "when the company sees a return / break-even",
  "budget_fit": "does it fit the stated budget and cash position",
  "financial_risks": ["risk 1", "risk 2"],
  "verdict": "FEASIBLE | STRETCH | INFEASIBLE"
}
"""


class FinanceAgent(BaseAgent):
    name = "finance"
    role = "Finance Agent — decision economics against the company P&L"

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        # Ground the analysis in the company's book financials (Xero/Shopify-style
        # connector). Mock-safe: returns a deterministic snapshot with no credentials,
        # and never crashes the pipeline.
        book = run_sync(mcp_client.fetch_financials(profile.company_name))
        metrics = book.get("metrics", {})
        book_block = "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in metrics.items())
        mcp_sources = book.get("sources", [])

        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            f"Book financials pulled from the company's accounting system "
            f"({book.get('period', 'recent')}):\n{book_block or '- (none available)'}\n\n"
            "Model the financial impact of this decision on THIS company, using the book "
            "figures above. Assess affordability, payback, and downside. Be realistic and conservative."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("financial_view", ""),
            score=data.get("feasibility_score"),
            key_findings=[
                data.get("payback_view", ""),
                data.get("budget_fit", ""),
            ],
            concerns=data.get("financial_risks", []),
            recommendations=[data.get("verdict", "")] if data.get("verdict") else [],
            raw_data={**data, "mcp_sources": mcp_sources},
        )
