"""
Shared test configuration for the FounderOS suite.

The test suite is hermetic: it must run keyless and offline, exercising the
mock fixtures of every agent / provider / MCP method. If a real QWEN_API_KEY
happens to be present in .env (live mode), unit tests would otherwise make
network calls and hang. We force mock mode for the whole session so the suite
behaves the same with or without credentials. A live smoke test (Sprint B) is
run deliberately and separately, never through this suite.
"""

import os

import pytest

# Rate limiting off for the hermetic suite — TestClient shares one client IP,
# so a real per-IP limit would 429 later analyze-tests. Must be set before
# backend.main is imported (the Limiter reads it at module import).
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from backend.config import settings
from backend.mcp.client import mcp_client
from backend.models import CompanyProfile, Financials, Decision, Constraints

# Force mock mode at import time — before any agent / provider is constructed.
settings.use_mock_llm = True
# The singleton computed .live at import; pin it to mock to stay offline.
mcp_client.live = False


@pytest.fixture
def company():
    """A representative existing company bringing a decision to the board."""
    return CompanyProfile(
        company_name="Kirana Logistics",
        sector="regional last-mile logistics",
        stage="scaling",
        business_model="B2B logistics SaaS + fleet ops",
        size_band="51–200",
        financials=Financials(
            revenue_band="SGD 8–12M ARR",
            margin="~22% gross",
            cash_position="14 months runway",
        ),
    )


@pytest.fixture
def decision():
    """One decision, with the alternatives on the table."""
    return Decision(
        question="Should we expand into the Vietnam market next quarter?",
        context="Two anchor customers have asked us to serve their Vietnam routes.",
        constraints=Constraints(budget="SGD 500k", timeline="6 months"),
        options=[
            "Full subsidiary in Ho Chi Minh City",
            "Asset-light partnership with a local 3PL",
            "Hold and deepen the current market",
        ],
    )


@pytest.fixture
def decision_no_options():
    """A decision with no options — Scout must frame them."""
    return Decision(
        question="Should we raise prices 15% across the B2B tier?",
        context="Margins are compressing and we haven't raised prices in two years.",
    )
