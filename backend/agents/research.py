import asyncio
import json
import logging
import re
from datetime import date
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

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
        """Base-class contract. Not on the hot path — analyze() builds a
        decision-aware fixture via _mock_data(); kept for any external caller."""
        return json.dumps(self._mock_data(
            CompanyProfile(company_name="Demo Co", sector="this sector",
                           stage="", business_model="", size_band=""),
            Decision(question="Is this decision sound?"),
        ))

    def _mock_data(self, profile: CompanyProfile, decision: Decision) -> Dict[str, Any]:
        """Deterministic, keyless, decision-aware fixture — templated on the
        company's sector and the question so a skincare decision never shows
        logistics numbers. Order-of-magnitude placeholders, clearly synthetic.

        Source labels carry a "[MOCK]" tag and cite mock.<sector>.example.com URLs
        (payload honesty); the display surfaces strip both (see cleanProse /
        stripMockMarkers on the frontend), and main.py filters the "[MOCK] "-
        prefixed mcp_sources out of research_sources, so nothing synthetic leaks."""
        sector = (profile.sector or "this sector").strip()
        question = (decision.question or "").strip()
        host = re.sub(r"[^a-z0-9]+", "-", sector.lower()).strip("-") or "sector"
        label = f"{sector} benchmark (synthetic) [MOCK]"

        def _dp(metric: str, value: str, slug: str) -> Dict[str, Any]:
            return {
                "metric": metric,
                "value": value,
                "geography": "primary market",
                "source_url": f"https://mock.{host}.example.com/{slug}",
                "source_label": label,
                "date_retrieved": "2026-07-09",
                "confidence": "low",
            }

        return {
            "summary": (
                f"Demo mode — synthetic {sector} benchmarks, not live data. "
                "Order-of-magnitude market size, growth, and cost figures are shown so the "
                "board has numbers to react to; add an API key for real, cited sources."
            ),
            "data_points": [
                _dp(f"{sector} — market size", "USD 2–5B (order-of-magnitude estimate)", "market-size"),
                _dp(f"{sector} — annual growth", "~8–14% CAGR", "growth-rate"),
                _dp(f"{sector} — cost / margin benchmark",
                    "operating costs typically 60–80% of revenue", "cost-benchmark"),
            ],
            "queries_used": [
                f"{sector} market size 2026",
                f"{sector} growth rate CAGR",
                f"{sector} cost benchmark",
                (question or f"{sector} outlook")[:80],
            ],
            "mcp_sources": [
                f"[MOCK] web: {sector} market size 2026",
                f"[MOCK] web: {sector} growth rate",
                f"[MOCK] news: {sector}",
                f"[MOCK] crunchbase: {sector}",
            ],
            "data_gaps": [
                f"No live sourcing in demo mode — {sector} figures are placeholders, "
                "not verified numbers.",
            ],
        }

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision: Decision = context["decision"]

        # Mock mode short-circuits before any LLM or MCP call — deterministic,
        # decision-aware fixture (templated on sector + question).
        if self.mock:
            return self._build_output(self._mock_data(profile, decision))

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
            data = self._parse_json(self.provider.chat(SYSTEM_PROMPT_QUERIES, user_message, 800))
            queries = [q for q in data.get("queries", []) if isinstance(q, str) and q.strip()]
        except json.JSONDecodeError as e:
            logger.warning("Research query generation: JSON parse failed — %s", e)
            queries = []
        except Exception as e:
            logger.exception("Research query generation: unexpected error — %s", e)
            queries = []

        if not queries:  # fallback — never leave the research pass with nothing to look up
            queries = [
                f"{profile.sector} {decision.question}".strip(),
                f"{profile.sector} market size 2026".strip(),
            ]
        return queries[:5]

    async def _gather_mcp(self, queries: List[str], profile: CompanyProfile) -> Dict[str, Any]:
        """Fan out web searches (one per query) + one news + one market lookup, in parallel."""
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
        except json.JSONDecodeError as e:
            logger.warning("Research extraction: JSON parse failed — %s", e)
            return {"summary": "", "data_points": [], "data_gaps": ["Research extraction failed."]}
        except Exception as e:
            logger.exception("Research extraction: unexpected error — %s", e)
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
