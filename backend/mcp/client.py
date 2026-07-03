"""
FounderOS — MCP Client (Phase 6)

Gives the agent society live market signals via an MCP tool server:
  - search_crunchbase(query)  — company / funding lookups
  - search_web(query)         — general web search
  - fetch_news(topic)         — recent news for a topic

Mock mode (default — no QWEN_API_KEY / no MCP server URL configured) returns
deterministic, realistically-shaped fixtures so the whole pipeline runs with
zero credentials. Live mode makes real async HTTP calls to the configured MCP
server and, on ANY failure, logs a warning and falls back to the mock — it
never crashes the pipeline.

Mock results carry sources prefixed with "[MOCK] " so callers (and the API
layer) can tell live data from fixtures.

A singleton `mcp_client` is exported at the bottom of the file.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ..config import settings

logger = logging.getLogger("founderos.mcp")

_MOCK_PREFIX = "[MOCK] "


# ─────────────────────────────────────────────
# Sync bridge — agents are synchronous (def analyze) but the MCP methods are
# async. This runs a coroutine to completion whether or not the caller already
# sits inside a running event loop (LangGraph runs sync nodes both ways).
# ─────────────────────────────────────────────

def run_sync(coro):
    """Run an async coroutine from synchronous code, safe under a running loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # no loop in this thread — just run it
    # A loop is already running in this thread — offload to a worker thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


class MCPClient:
    """Async MCP client with a deterministic mock fallback."""

    def __init__(self):
        # Live only when there is a key, mock is off, AND an MCP server is set.
        self.live: bool = settings.is_live and bool(settings.mcp_server_url)

    # ──────────────────────────────────────────
    # Public async API
    # ──────────────────────────────────────────

    async def search_crunchbase(self, query: str) -> Dict[str, Any]:
        """Look up companies / funding for `query`."""
        if not self.live:
            return self._mock_crunchbase(query)
        try:
            data = await self._post("crunchbase/search", {"query": query})
            return self._normalize(data, mode="live", query=query,
                                   default_sources=[f"crunchbase:{query}"])
        except Exception as e:  # never crash the pipeline
            logger.warning("MCP search_crunchbase('%s') failed (%s); using mock fallback", query, e)
            return self._mock_crunchbase(query)

    async def search_web(self, query: str) -> Dict[str, Any]:
        """General web search for `query`."""
        if not self.live:
            return self._mock_web(query)
        try:
            data = await self._post("web/search", {"query": query})
            return self._normalize(data, mode="live", query=query,
                                   default_sources=[f"web:{query}"])
        except Exception as e:
            logger.warning("MCP search_web('%s') failed (%s); using mock fallback", query, e)
            return self._mock_web(query)

    async def fetch_news(self, topic: str) -> Dict[str, Any]:
        """Recent news articles for `topic`."""
        if not self.live:
            return self._mock_news(topic)
        try:
            data = await self._post("news/fetch", {"topic": topic})
            return self._normalize(data, mode="live", query=topic,
                                   default_sources=[f"news:{topic}"])
        except Exception as e:
            logger.warning("MCP fetch_news('%s') failed (%s); using mock fallback", topic, e)
            return self._mock_news(topic)

    async def fetch_financials(self, company: str) -> Dict[str, Any]:
        """Pull `company`'s book financials (a Xero/Shopify-style accounting snapshot)."""
        if not self.live:
            return self._mock_financials(company)
        try:
            data = await self._post("accounting/financials", {"company": company})
            return self._normalize(data, mode="live", query=company,
                                   default_sources=[f"accounting:{company}"])
        except Exception as e:  # never crash the pipeline
            logger.warning("MCP fetch_financials('%s') failed (%s); using mock fallback", company, e)
            return self._mock_financials(company)

    # ──────────────────────────────────────────
    # Live HTTP
    # ──────────────────────────────────────────

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        import httpx  # lazy — mock mode needs no HTTP stack

        url = f"{settings.mcp_server_url.rstrip('/')}/{path}"
        headers = {"Authorization": f"Bearer {settings.qwen_api_key}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _normalize(data: Dict[str, Any], *, mode: str, query: str,
                   default_sources: list[str]) -> Dict[str, Any]:
        """Ensure a live response carries the fields callers rely on."""
        data.setdefault("mode", mode)
        data.setdefault("query", query)
        data.setdefault("sources", default_sources)
        return data

    # ──────────────────────────────────────────
    # Deterministic mock fixtures (query-seeded, non-empty)
    # ──────────────────────────────────────────

    @staticmethod
    def _mock_crunchbase(query: str) -> Dict[str, Any]:
        return {
            "query": query,
            "mode": "mock",
            "results": [
                {
                    "name": f"{query.title()} Labs",
                    "description": f"Early-stage startup operating in the {query} space.",
                    "funding_total": "USD 2.4M",
                    "last_round": "Seed",
                    "investors": ["Antler", "500 Global"],
                    "founded": "2024",
                    "url": "https://www.crunchbase.com/organization/example",
                },
                {
                    "name": f"{query.title()} Hub",
                    "description": f"Growth-stage player serving the {query} market in SEA.",
                    "funding_total": "USD 11M",
                    "last_round": "Series A",
                    "investors": ["Sequoia SEA", "East Ventures"],
                    "founded": "2022",
                    "url": "https://www.crunchbase.com/organization/example-2",
                },
            ],
            "sources": [f"{_MOCK_PREFIX}crunchbase: {query}"],
        }

    @staticmethod
    def _mock_web(query: str) -> Dict[str, Any]:
        return {
            "query": query,
            "mode": "mock",
            "results": [
                {
                    "title": f"The state of {query}",
                    "snippet": f"Demand for {query} continues to accelerate heading into 2026.",
                    "url": "https://example.com/report",
                },
                {
                    "title": f"{query.title()}: what founders should know",
                    "snippet": f"Key shifts and emerging gaps across the {query} landscape.",
                    "url": "https://example.com/analysis",
                },
            ],
            "sources": [f"{_MOCK_PREFIX}web: {query}"],
        }

    @staticmethod
    def _mock_news(topic: str) -> Dict[str, Any]:
        return {
            "topic": topic,
            "mode": "mock",
            "articles": [
                {
                    "headline": f"Investors double down on {topic} startups",
                    "summary": f"Capital is flowing into {topic} as adoption widens.",
                    "source": "TechCrunch",
                    "published": "2026-06-01",
                    "url": "https://example.com/news/1",
                },
                {
                    "headline": f"New regulations reshape the {topic} market",
                    "summary": f"Policy changes create fresh openings in {topic}.",
                    "source": "Reuters",
                    "published": "2026-05-18",
                    "url": "https://example.com/news/2",
                },
            ],
            "sources": [f"{_MOCK_PREFIX}news: {topic}"],
        }

    @staticmethod
    def _mock_financials(company: str) -> Dict[str, Any]:
        return {
            "company": company,
            "mode": "mock",
            "period": "trailing 12 months",
            "metrics": {
                "revenue": "SGD 9.8M",
                "revenue_growth_yoy": "+18%",
                "gross_margin": "31%",
                "operating_expenses": "SGD 6.1M",
                "net_profit_margin": "6%",
                "cash_on_hand": "SGD 2.3M",
                "monthly_burn": "SGD 140k",
                "runway_months": 16,
            },
            "sources": [f"{_MOCK_PREFIX}accounting: {company}"],
        }


# Singleton — import this everywhere.
mcp_client = MCPClient()
