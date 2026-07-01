"""
Vault tests (Decision #1: vault only) — file-backed, offline, no DB.

Covers: empty-vault read, write_back creating a decision note, selective
retrieval picking the relevant note, the outcome loop, and the full HTTP flow
(analyze → response → feedback → company history). VAULT_PATH is pointed at a
tmp dir so tests never touch a real vault.

Fixtures `company`, `decision` live in conftest.py.
"""

import pytest
from fastapi.testclient import TestClient

from backend.vault.store import Vault
from backend.models import Decision, Constraints
from backend.main import app


@pytest.fixture
def vault(tmp_path):
    return Vault(root=str(tmp_path))


# ── read / write_back ─────────────────────────────────────────────────────────

def test_empty_vault_returns_empty_bundle(vault):
    bundle = vault.read("new-co", "any question")
    assert bundle.notes == []
    assert bundle.used_paths == []
    assert "first session" in bundle.as_prompt_block().lower()


def test_write_back_creates_a_decision_note(vault, decision):
    from backend.models import BoardRecommendation
    rec = BoardRecommendation(
        recommendation="conditional", confidence="medium",
        rationale="Go asset-light first.", missing_inputs=["signed volumes"],
    )
    decision_id = vault.write_back("kirana", decision, rec, learnings=["demand unproven"])
    assert decision_id

    index = vault.index("kirana")
    assert len(index) == 1
    assert index[0].frontmatter["recommendation"] == "conditional"
    assert index[0].frontmatter["decision_id"] == decision_id
    assert index[0].summary


def test_selective_retrieval_picks_relevant_note(vault):
    from backend.models import BoardRecommendation
    rec = BoardRecommendation(recommendation="proceed", confidence="high", rationale="x")

    vault.write_back("kirana",
                     Decision(question="Should we expand into Vietnam logistics?"), rec)
    vault.write_back("kirana",
                     Decision(question="Should we replace our payroll vendor?"), rec)

    bundle = vault.read("kirana", "expand into Vietnam market")
    assert bundle.used_paths                       # something selected
    assert any("Vietnam" in note for note in bundle.notes)


def test_outcome_loop_writes_back(vault, decision):
    from backend.models import BoardRecommendation
    rec = BoardRecommendation(recommendation="proceed", confidence="high", rationale="x")
    decision_id = vault.write_back("kirana", decision, rec)

    assert vault.record_outcome("kirana", decision_id, "launched", "went live in Q3") is True
    # The outcome is now in the note body + index frontmatter.
    hist = vault.history("kirana")
    assert hist[0]["outcome"].startswith("launched")


def test_record_outcome_unknown_decision_returns_false(vault):
    assert vault.record_outcome("kirana", "does-not-exist", "launched") is False


# ── Full HTTP flow ────────────────────────────────────────────────────────────

@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    """Point the module-level vault singleton at a tmp dir for API tests."""
    from backend.vault import store
    monkeypatch.setattr(store._vault, "root", tmp_path)
    return tmp_path


def test_analyze_response_feedback_company_flow(company, decision, isolated_vault):
    client = TestClient(app)

    # 1. Analyze — evaluate the decision.
    r = client.post("/api/analyze", json={
        "company_id": "kirana",
        "profile": company.model_dump(),
        "decision": decision.model_dump(),
    })
    assert r.status_code == 200, r.text
    body = r.json()
    response_id = body["response_id"]
    assert body["recommendation"]["recommendation"] in ("proceed", "hold", "conditional")

    # 2. Fetch the saved response.
    got = client.get(f"/api/response/{response_id}")
    assert got.status_code == 200
    assert got.json()["response_id"] == response_id

    # 3. The decision is now in the company's vault history.
    hist = client.get("/api/company/kirana").json()["history"]
    assert len(hist) == 1
    assert hist[0]["outcome"] == ""   # pending until feedback

    # 4. Feedback — the outcome loop writes back.
    fb = client.post("/api/feedback", json={
        "response_id": response_id,
        "outcome": "proceeded asset-light",
        "notes": "signed one anchor customer",
    })
    assert fb.status_code == 200
    assert fb.json()["written_to_vault"] is True

    hist2 = client.get("/api/company/kirana").json()["history"]
    assert hist2[0]["outcome"].startswith("proceeded")


def test_feedback_unknown_response_404(isolated_vault):
    client = TestClient(app)
    resp = client.post("/api/feedback", json={
        "response_id": "does-not-exist", "outcome": "launched",
    })
    assert resp.status_code == 404


def test_second_run_reads_prior_history(company, decision, isolated_vault):
    """A returning company: the board sees its own prior decision on the next run."""
    client = TestClient(app)
    client.post("/api/analyze", json={                   # session 1 persists a note
        "company_id": "kirana",
        "profile": company.model_dump(),
        "decision": decision.model_dump(),
    })

    from backend.vault import store
    bundle = store.read("kirana", decision.question)
    assert bundle.used_paths                              # prior note retrieved
