"""
MCP integration tests (mock mode, no credentials, offline).

Covers: the MCPClient mock schema for all three methods, Scout/Trend surfacing
mcp_sources, and the /api/analyze response exposing mcp_used + mcp_sources.
The suite is forced into mock mode by backend/tests/conftest.py.

Fixtures `company`, `decision` live in conftest.py.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.mcp.client import MCPClient
from backend.agents import OpportunityScoutAgent, TrendAnalystAgent, FinanceAgent
from backend.main import app


def _run(coro):
    return asyncio.run(coro)


# ── MCPClient mock schema ─────────────────────────────────────────────────────

def test_mcp_client_is_mock_without_mcp_server():
    """No mcp_server_url configured → client is in mock mode."""
    client = MCPClient()
    assert client.live is False


def test_search_crunchbase_mock_schema():
    client = MCPClient()
    data = _run(client.search_crunchbase("logistics"))
    assert data["mode"] == "mock"
    assert data["query"] == "logistics"
    assert isinstance(data["results"], list) and data["results"]
    first = data["results"][0]
    for key in ("name", "description", "funding_total", "last_round", "investors", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]
    assert all(s.startswith("[MOCK] ") for s in data["sources"])


def test_search_web_mock_schema():
    client = MCPClient()
    data = _run(client.search_web("logistics trends 2026"))
    assert data["mode"] == "mock"
    assert isinstance(data["results"], list) and data["results"]
    first = data["results"][0]
    for key in ("title", "snippet", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]


def test_fetch_news_mock_schema():
    client = MCPClient()
    data = _run(client.fetch_news("logistics"))
    assert data["mode"] == "mock"
    assert data["topic"] == "logistics"
    assert isinstance(data["articles"], list) and data["articles"]
    first = data["articles"][0]
    for key in ("headline", "summary", "source", "published", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]


def test_fetch_financials_mock_schema():
    client = MCPClient()
    data = _run(client.fetch_financials("Harborline Logistics"))
    assert data["mode"] == "mock"
    assert data["company"] == "Harborline Logistics"
    assert isinstance(data["metrics"], dict) and data["metrics"]
    for key in ("revenue", "gross_margin", "cash_on_hand", "runway_months"):
        assert key in data["metrics"]
    assert isinstance(data["sources"], list) and data["sources"]
    assert all(s.startswith("[MOCK] ") for s in data["sources"])


def test_mock_is_deterministic():
    client = MCPClient()
    a = _run(client.search_crunchbase("fintech"))
    b = _run(client.search_crunchbase("fintech"))
    assert a == b
    # financials snapshot is deterministic too
    assert _run(client.fetch_financials("Acme")) == _run(client.fetch_financials("Acme"))


# ── Scout surfaces mcp_sources ────────────────────────────────────────────────

def test_scout_output_has_mcp_sources(company, decision):
    out = OpportunityScoutAgent().analyze(company, {"decision": decision})
    assert "mcp_sources" in out.raw_data
    assert isinstance(out.raw_data["mcp_sources"], list)
    assert out.raw_data["mcp_sources"]


# ── Trend surfaces mcp_sources ────────────────────────────────────────────────

def test_trend_output_has_mcp_sources(company, decision):
    out = TrendAnalystAgent().analyze(company, {"decision": decision})
    assert "mcp_sources" in out.raw_data
    assert isinstance(out.raw_data["mcp_sources"], list)


# ── Finance surfaces mcp_sources from the financials connector ─────────────────

def test_finance_output_has_mcp_sources(company, decision):
    out = FinanceAgent().analyze(company, {"decision": decision})
    assert "mcp_sources" in out.raw_data
    assert isinstance(out.raw_data["mcp_sources"], list) and out.raw_data["mcp_sources"]
    assert any("accounting" in s for s in out.raw_data["mcp_sources"])


# ── /api/analyze exposes mcp_used + mcp_sources ───────────────────────────────

def test_analyze_response_has_mcp_fields(company, decision, tmp_path, monkeypatch):
    from backend.vault import store
    monkeypatch.setattr(store._vault, "root", tmp_path)

    client = TestClient(app)
    r = client.post("/api/analyze", json={
        "company_id": "kirana-logistics",
        "profile": company.model_dump(),
        "decision": decision.model_dump(),
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "mcp_used" in body and isinstance(body["mcp_used"], bool)
    assert "mcp_sources" in body and isinstance(body["mcp_sources"], list)
    assert body["mcp_used"] is False   # mock mode → no live data
    assert body["mcp_sources"]
