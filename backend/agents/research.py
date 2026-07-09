import json
from datetime import date
from typing import Dict, Any, List

from .base import BaseAgent
from ..models import CompanyProfile, Decision, AgentOutput
from ..mcp.client import mcp_client, run_sync

# The Research agent ("Market Intelligence") fetches real-world numbers — land
# prices, logistics rates, market sizes, competitor pricing — that ground the
# board memo in fact rather than assumption. It runs AFTER Scout frames the
# options and BEFORE the analysts fan out, handing each analyst a structured
# brief. Its job is data fetching and citation, not analysis.
#
# Canonical string `research`; displays as "Market Intelligence".

_MOCK = json.dumps({
    "summary": (
        "Real-world benchmarks point to a viable but capital-sensitive move: warehouse "
        "space runs USD 12–18/sqm/month and last-mile 3PL rates USD 2.50–4.00/kg in a "
        "market growing ~14% a year. The one gap is customs clearance cost per shipment."
    ),
    "data_points": [
        {
            "metric": "warehouse lease rate",
            "value": "USD 12–18 per sqm/month",
            "geography": "Ho Chi Minh City, Vietnam",
            "source_url": "https://mock.research.example.com/cbre-vietnam-industrial-2025",
            "source_label": "CBRE Vietnam Industrial Market Q3 2025 [MOCK]",
            "date_retrieved": "2026-07-09",
            "confidence": "medium",
        },
        {
            "metric": "last-mile delivery rate (3PL partnership)",
            "value": "USD 2.50–4.00 per kg",
            "geography": "Vietnam (national)",
            "source_url": "https://mock.research.example.com/statista-vietnam-logistics-2025",
            "source_label": "Statista Vietnam Logistics Report 2025 [MOCK]",
            "date_retrieved": "2026-07-09",
            "confidence": "medium",
        },
        {
            "metric": "logistics market size",
            "value": "USD 40B, 14% CAGR",
            "geography": "Vietnam",
            "source_url": "https://mock.research.example.com/researchandmarkets-vn-logistics",
            "source_label": "ResearchAndMarkets Vietnam Logistics 2025 [MOCK]",
            "date_retrieved": "2026-07-09",
            "confidence": "low",
        },
        {
            "metric": "competitor last-mile pricing benchmark",
            "value": "SGD 0.80–1.20 per delivery (SEA average)",
            "geography": "Southeast Asia",
            "source_url": "https://mock.research.example.com/sea-logistics-benchmark-2025",
            "source_label": "SEA Logistics Benchmark Report 2025 [MOCK]",
            "date_retrieved": "2026-07-09",
            "confidence": "low",
        },
    ],
    "queries_used": [
        "warehouse lease price per sqm Ho Chi Minh City 2025",
        "Vietnam 3PL last-mile delivery rates 2025",
        "Vietnam logistics market size growth CAGR",
        "competitor last-mile delivery pricing Southeast Asia",
    ],
    "mcp_sources": [
        "[MOCK] web: warehouse lease price per sqm Ho Chi Minh City 2025",
        "[MOCK] web: Vietnam 3PL last-mile delivery rates 2025",
        "[MOCK] news: Vietnam logistics market",
        "[MOCK] crunchbase: logistics",
    ],
    "data_gaps": [
        "No usable data on customs clearance cost per shipment in Vietnam — "
        "queries returned generic regulatory pages only",
    ],
})


SYSTEM_PROMPT_QUERIES = """
You are the Market Intelligence researcher on an AI board advising an EXISTING company on
ONE decision. Your task here is narrow: generate 3–5 targeted web search queries that would
surface REAL-WORLD NUMBERS relevant to this decision.

Good queries are specific. Include, where relevant: country/city/market names, unit types
(price per sqm, rate per km, USD or SGD), and a recent year (2025 or 2026). Aim for quantifiable
facts — prices, rates, distances, market sizes, benchmarks, regulatory costs — not opinion.

Never invent names, companies, products, or agreements the operator did not provide — refer to unnamed entities exactly as the operator did (e.g. "the third shipper").

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "queries": ["query 1", "query 2", "query 3"]
}
"""


SYSTEM_PROMPT_EXTRACT = """
You are the Market Intelligence researcher on an AI board. You are given raw web/news/market
search results. Extract the concrete, quantifiable DATA POINTS that bear on the decision —
real numbers with their source URL. Do NOT analyse or recommend; just pull and structure facts.

For each data point capture: what was measured (metric), the number with units (value), where
it applies (geography), the source URL and a short source label, and your confidence:
- "high"   — a specific figure from a named source with a date
- "medium" — a range, or a number from a source without a clear date
- "low"    — a proxy figure, inferred, or from a thin/unclear source

Only use URLs that appear in the provided results — never fabricate a link. If a query area
returned nothing usable, record it under data_gaps. Write a one-paragraph summary of the
headline numbers and the biggest gap.

Never invent names, companies, products, or agreements the operator did not provide — refer to unnamed entities exactly as the operator did (e.g. "the third shipper").

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "summary": "one paragraph: the headline numbers found and the biggest data gap",
  "data_points": [
    {
      "metric": "string",
      "value": "number with units",
      "geography": "string",
      "source_url": "https://...",
      "source_label": "short source name",
      "confidence": "high | medium | low"
    }
  ],
  "data_gaps": ["areas where research came back thin"]
}
"""


class MarketResearchAgent(BaseAgent):
    name = "research"
    role = "Market Intelligence — real-world data brief for the board"
    max_tokens = 3000

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision: Decision = context["decision"]

        # Mock mode short-circuits before any LLM or MCP call — deterministic fixture.
        if self.mock:
            return self._build_output(json.loads(self._mock_response()))

        # 1. Generate the search queries from the decision + framed options.
        queries = self._generate_queries(profile, decision)

        # 2. Fan out the MCP calls in parallel and collect a raw block + provenance.
        gathered = run_sync(self._gather_mcp(queries, profile))

        # 3. Extract structured data points from the raw results.
        extracted = self._extract(gathered["block"], decision)

        today = date.today().isoformat()
        data_points = []
        for dp in extracted.get("data_points", []):
            if isinstance(dp, dict):
                dp.setdefault("date_retrieved", today)
                data_points.append(dp)

        data = {
            "summary": extracted.get("summary", ""),
            "data_points": data_points,
            "queries_used": queries,
            "mcp_sources": gathered["sources"],
            "data_gaps": extracted.get("data_gaps", []),
        }
        return self._build_output(data)

    # ──────────────────────────────────────────
    # Steps
    # ──────────────────────────────────────────

    def _generate_queries(self, profile: CompanyProfile, decision: Decision) -> List[str]:
        """One FAST_MODEL call → 3–5 targeted search queries (with a safe fallback)."""
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)
        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            "Generate 3–5 targeted web search queries that would surface real-world numbers "
            "for this decision."
        )
        try:
            data = self._parse_json(self.provider.chat(SYSTEM_PROMPT_QUERIES, user_message, 500))
            queries = [q for q in data.get("queries", []) if isinstance(q, str) and q.strip()]
        except (ValueError, Exception):
            queries = []

        if not queries:  # fallback — never leave the research pass with nothing to look up
            queries = [
                f"{profile.sector} {decision.question}".strip(),
                f"{profile.sector} market size 2026".strip(),
            ]
        return queries[:5]

    async def _gather_mcp(self, queries: List[str], profile: CompanyProfile) -> Dict[str, Any]:
        """Fan out web searches (one per query) + one news + one market lookup, in parallel."""
        import asyncio

        sector = profile.sector or (queries[0] if queries else "")
        tasks = [mcp_client.search_web(q) for q in queries]
        tasks.append(mcp_client.fetch_news(sector))
        tasks.append(mcp_client.search_crunchbase(sector))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        lines: List[str] = []
        sources: List[str] = []
        for res in results:
            if isinstance(res, Exception) or not isinstance(res, dict):
                continue
            sources.extend(res.get("sources", []))
            for r in res.get("results", []):
                lines.append(
                    f"- {r.get('title', '')}: {r.get('snippet', '')} "
                    f"[{r.get('url', '')}]"
                )
            for a in res.get("articles", []):
                lines.append(
                    f"- {a.get('headline', '')}: {a.get('summary', '')} "
                    f"({a.get('source', '')}, {a.get('published', '')}) [{a.get('url', '')}]"
                )

        return {
            "block": "\n".join(lines) or "No results returned.",
            "sources": list(dict.fromkeys(sources)),  # dedupe, order-preserving
        }

    def _extract(self, raw_block: str, decision: Decision) -> Dict[str, Any]:
        """One FAST_MODEL call → structured data points from the raw results."""
        user_message = (
            f"Decision on the table: {decision.question}\n\n"
            "## Raw search results\n"
            f"{raw_block}\n\n"
            "Extract the quantifiable data points that bear on this decision."
        )
        try:
            return self._parse_json(self.provider.chat(SYSTEM_PROMPT_EXTRACT, user_message, self.max_tokens))
        except (ValueError, Exception):
            return {"summary": "", "data_points": [], "data_gaps": ["Research extraction failed."]}

    # ──────────────────────────────────────────
    # Output
    # ──────────────────────────────────────────

    def _build_output(self, data: Dict[str, Any]) -> AgentOutput:
        data_points = [dp for dp in data.get("data_points", []) if isinstance(dp, dict)]
        key_findings = [
            f"{dp.get('metric', '')}: {dp.get('value', '')}"
            + (f" ({dp.get('source_label', '')})" if dp.get("source_label") else "")
            for dp in data_points
        ]
        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("summary", ""),
            score=None,
            key_findings=key_findings,
            concerns=data.get("data_gaps", []),
            recommendations=[],
            raw_data={
                "data_points": data_points,
                "queries_used": data.get("queries_used", []),
                "mcp_sources": data.get("mcp_sources", []),
                "data_gaps": data.get("data_gaps", []),
            },
        )
