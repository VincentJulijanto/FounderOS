"""
Whole-system hardening tests — offline, mock-only, no LLM/API calls.

Fills two gaps the per-module suites don't cover:
  1. The committed **seed vault** (vault/harborline-logistics, vault/lumen-skincare)
     is what the demo's "a returning company remembers" beat runs on. A malformed
     seed note (bad frontmatter, missing summary/outcome) would break that silently.
  2. The **frontend↔backend contract** is the pivot's gate. These tests lock the
     backend models and the canonical agent-name strings against what the frontend
     (lib/types.ts, BoardMemo.tsx, agentRoster.tsx) reads — the exact coupling that
     broke in the Phase 4 roster mismatch.

Everything here is hermetic (conftest pins mock mode); the API path is exercised
only against mock fixtures, never a live model.
"""

import re
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.vault.store import Vault
from backend.models import BoardRecommendation, BoardResponse
from backend.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_VAULT = REPO_ROOT / "vault"
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

SEEDED_COMPANIES = ["harborline-logistics", "lumen-skincare"]
CANONICAL_AGENTS = ["scout", "trend", "finance", "growth", "skeptic", "capability", "venture_partner"]

VALID_RECS = {"proceed", "hold", "conditional"}
VALID_CONF = {"low", "medium", "high"}


# ── 1. Seed vault integrity ───────────────────────────────────────────────────

@pytest.mark.parametrize("company_id", SEEDED_COMPANIES)
def test_seed_vault_notes_are_well_formed(company_id):
    """Every committed seed note must parse and carry valid, rankable frontmatter."""
    v = Vault(root=str(SEED_VAULT))
    index = v.index(company_id)
    assert index, f"seed company {company_id!r} has no notes — the demo beat needs history"

    for note in index:
        fm = note.frontmatter
        assert fm.get("type") == "decision", f"{note.path}: type must be 'decision'"
        assert fm.get("decision_id"), f"{note.path}: missing decision_id"
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", fm.get("date", "")), f"{note.path}: bad date"
        assert fm.get("recommendation") in VALID_RECS, f"{note.path}: bad recommendation"
        assert fm.get("confidence") in VALID_CONF, f"{note.path}: bad confidence"
        assert note.summary.strip(), f"{note.path}: empty summary — selector can't rank it"

    # The memory beat needs at least one *recorded outcome* (decision → later outcome).
    assert any(n.frontmatter.get("outcome", "").strip() for n in index), \
        f"{company_id}: no recorded outcome — nothing for the board to 'remember'"


def test_seed_company_history_is_retrievable():
    """Read-only: the seed history is selectable and date-sorted (no writes to the seed)."""
    v = Vault(root=str(SEED_VAULT))
    bundle = v.read("harborline-logistics", "should we open a new cross-border lane")
    assert bundle.used_paths, "selector returned nothing for a clearly-related query"
    assert any("Vietnam" in n or "lane" in n.lower() for n in bundle.notes)

    hist = v.history("harborline-logistics")
    assert len(hist) == 5  # seed depth raised to 5 so live _llm_select can fire (>4 notes)
    dates = [h["date"] for h in hist]
    assert dates == sorted(dates, reverse=True), "history must be newest-first"


# ── 2. Frontend↔backend contract shape ────────────────────────────────────────

def test_board_models_expose_every_field_the_frontend_reads():
    """Backend models must carry exactly the fields BoardMemo.tsx / page.tsx render."""
    frontend_rec_fields = {
        "recommendation", "confidence", "rationale", "missing_inputs", "options_assessed",
        "dissent", "what_would_change_this_call", "execution_plan", "financial_view",
        "risks", "disclaimer",
    }
    frontend_response_fields = {
        "response_id", "company_id", "agent_outputs", "debate_rounds", "consensus",
        "recommendation", "mcp_used", "mcp_sources",
    }
    missing_rec = frontend_rec_fields - set(BoardRecommendation.model_fields)
    missing_resp = frontend_response_fields - set(BoardResponse.model_fields)
    assert not missing_rec, f"BoardRecommendation missing frontend fields: {missing_rec}"
    assert not missing_resp, f"BoardResponse missing frontend fields: {missing_resp}"


def test_frontend_mirror_stays_aligned_with_backend():
    """The frontend roster + type mirror must track the canonical contract."""
    roster = (FRONTEND_SRC / "components" / "agentRoster.tsx").read_text(encoding="utf-8")
    for name in CANONICAL_AGENTS:
        assert f"name: '{name}'" in roster, f"agentRoster.tsx lost canonical key {name!r}"
    # venture_partner must still display as the human-facing "Chair".
    assert "label: 'Chair'" in roster, "venture_partner must display as 'Chair'"

    types_ts = (FRONTEND_SRC / "lib" / "types.ts").read_text(encoding="utf-8")
    for iface in ("BoardResponse", "BoardRecommendation", "AgentOutput", "Decision"):
        assert f"interface {iface}" in types_ts, f"lib/types.ts missing {iface}"


# ── 3. Returning-company end-to-end on an isolated copy of the seed ────────────

def test_returning_company_end_to_end_on_seed_copy(tmp_path, monkeypatch):
    """
    The full demo beat, offline: a company with seed history brings a new decision,
    the board retrieves its own past, and the new decision is appended. Runs on a
    COPY of the seed so write-back never mutates the committed vault.
    """
    shutil.copytree(SEED_VAULT / "harborline-logistics", tmp_path / "harborline-logistics")
    from backend.vault import store
    monkeypatch.setattr(store._vault, "root", tmp_path)

    # The board sees its own prior decisions.
    bundle = store.read("harborline-logistics", "expand into another cross-border lane")
    assert bundle.used_paths, "returning company: prior seed notes not retrieved"

    # A new decision runs end-to-end (mock) and is written back.
    client = TestClient(app)
    r = client.post("/api/analyze", json={
        "company_id": "harborline-logistics",
        "decision": {"question": "Should we add a Thailand cross-border lane?", "constraints": {}},
    })
    assert r.status_code == 200, r.text

    hist = client.get("/api/company/harborline-logistics").json()["history"]
    assert len(hist) == 6, "expected 5 seed notes + 1 newly written decision"
