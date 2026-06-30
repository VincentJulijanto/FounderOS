"""
Phase 6 — MCP integration tests (mock mode, no credentials, offline).

Covers: the MCPClient mock schema for all three methods, Scout/Trend surfacing
mcp_sources, and the /api/analyze response exposing mcp_used + mcp_sources.
The suite is forced into mock mode by backend/tests/conftest.py.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from backend.mcp.client import MCPClient
from backend.agents import OpportunityScoutAgent, TrendAnalystAgent
from backend.models import UserProfile
from backend.main import app


@pytest.fixture
def founder():
    return UserProfile(
        user_id="mcp-founder",
        name="Alex Tan",
        background="NUS CS student",
        skills=["Python", "React"],
        budget=500,
        weekly_hours=10,
        interests=["edtech"],
        goals="SGD 2,000/month side income",
    )


def _run(coro):
    return asyncio.run(coro)


# ── Task 5.1 — MCPClient mock schema ─────────────────────────────────────────

def test_mcp_client_is_mock_without_mcp_server():
    """No mcp_server_url configured → client is in mock mode."""
    client = MCPClient()
    assert client.live is False


def test_search_crunchbase_mock_schema():
    client = MCPClient()
    data = _run(client.search_crunchbase("edtech"))
    assert data["mode"] == "mock"
    assert data["query"] == "edtech"
    assert isinstance(data["results"], list) and data["results"]  # non-empty
    first = data["results"][0]
    for key in ("name", "description", "funding_total", "last_round", "investors", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]
    assert all(s.startswith("[MOCK] ") for s in data["sources"])


def test_search_web_mock_schema():
    client = MCPClient()
    data = _run(client.search_web("edtech trends 2026"))
    assert data["mode"] == "mock"
    assert isinstance(data["results"], list) and data["results"]
    first = data["results"][0]
    for key in ("title", "snippet", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]


def test_fetch_news_mock_schema():
    client = MCPClient()
    data = _run(client.fetch_news("edtech"))
    assert data["mode"] == "mock"
    assert data["topic"] == "edtech"
    assert isinstance(data["articles"], list) and data["articles"]
    first = data["articles"][0]
    for key in ("headline", "summary", "source", "published", "url"):
        assert key in first
    assert isinstance(data["sources"], list) and data["sources"]


def test_mock_is_deterministic():
    client = MCPClient()
    a = _run(client.search_crunchbase("fintech"))
    b = _run(client.search_crunchbase("fintech"))
    assert a == b


# ── Task 5.2 — Scout surfaces mcp_sources ────────────────────────────────────

def test_scout_output_has_mcp_sources(founder):
    out = OpportunityScoutAgent().analyze(founder)
    assert "mcp_sources" in out.raw_data
    assert isinstance(out.raw_data["mcp_sources"], list)
    assert out.raw_data["mcp_sources"]  # mock labels present


# ── Task 5.3 — Trend surfaces mcp_sources ────────────────────────────────────

def test_trend_output_has_mcp_sources(founder):
    scout = OpportunityScoutAgent().analyze(founder)
    out = TrendAnalystAgent().analyze(
        founder, {"opportunities": scout.raw_data["opportunities"]}
    )
    assert "mcp_sources" in out.raw_data
    assert isinstance(out.raw_data["mcp_sources"], list)


# ── Task 5.4 — /api/analyze exposes mcp_used + mcp_sources ────────────────────

def test_analyze_response_has_mcp_fields(founder):
    client = TestClient(app)
    r = client.post("/api/analyze", json={"profile": founder.model_dump()})
    assert r.status_code == 200
    body = r.json()
    assert "mcp_used" in body and isinstance(body["mcp_used"], bool)
    assert "mcp_sources" in body and isinstance(body["mcp_sources"], list)
    # mock mode → no live data
    assert body["mcp_used"] is False
    # union of Scout + Trend sources, deduped
    assert body["mcp_sources"]
