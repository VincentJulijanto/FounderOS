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


def test_identical_same_day_decisions_do_not_collide(vault):
    """Two identical same-day decisions must not overwrite each other (regression)."""
    from backend.models import BoardRecommendation
    rec = BoardRecommendation(recommendation="hold", confidence="low", rationale="x")
    q = Decision(question="Should we do the exact same thing?")

    id1 = vault.write_back("co", q, rec)
    id2 = vault.write_back("co", q, rec)
    assert id1 != id2
    assert len(vault.index("co")) == 2, "identical same-day decisions overwrote each other"
    # Both decision_ids stay independently addressable for the outcome loop.
    assert vault.record_outcome("co", id1, "outcome one") is True
    assert vault.record_outcome("co", id2, "outcome two") is True


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


def test_slug_never_cuts_mid_word():
    from backend.vault.store import _slugify, _MAX_SLUG_LEN

    q = "Should we scale the Vietnam cross-border lane beyond the pilot programme this year"
    slug = _slugify(q)
    full = q.lower().replace(" ", "-")  # the uncapped slug of the same question
    assert len(slug) <= _MAX_SLUG_LEN
    assert not slug.endswith("-")
    # The cap must land on a word boundary: the full slug continues with "-",
    # never with the rest of a split word.
    assert full.startswith(slug)
    assert full == slug or full[len(slug)] == "-"
    # Short questions are untouched; empty input still yields a filename.
    assert _slugify("Raise rates?") == "raise-rates"
    assert _slugify("???") == "decision"


# ── company profile note (_profile.md) ────────────────────────────────────────

def _rec():
    from backend.models import BoardRecommendation
    return BoardRecommendation(recommendation="proceed", confidence="high", rationale="x")


def test_write_back_persists_profile_note(vault, company, decision):
    from backend.vault.store import PROFILE_NOTE, _parse_frontmatter

    vault.write_back("kirana", decision, _rec(), profile=company)

    raw = (vault.root / "kirana" / PROFILE_NOTE).read_text(encoding="utf-8")
    fm, _body = _parse_frontmatter(raw)
    assert fm["type"] == "profile"
    assert fm["updated"]
    assert vault.read_profile("kirana") == company          # lossless round-trip
    # Identity note never enters the rankable index.
    assert all(n.path != PROFILE_NOTE for n in vault.index("kirana"))


def test_changed_profile_updates_note(vault, company, decision):
    from backend.vault.store import PROFILE_NOTE

    vault.write_back("kirana", decision, _rec(), profile=company)
    changed = company.model_copy(update={"stage": "mature"})
    vault.write_back("kirana", decision, _rec(), profile=changed)

    assert len(list((vault.root / "kirana").glob(PROFILE_NOTE))) == 1
    assert vault.read_profile("kirana").stage == "mature"


def test_read_includes_profile_outside_selection_budget(vault, company):
    from backend.vault.store import MAX_SELECTED_NOTES, PROFILE_NOTE

    vault.write_profile("kirana", company)
    for i in range(MAX_SELECTED_NOTES + 2):
        vault.write_back("kirana", Decision(question=f"Should we expand into market {i}?"), _rec())

    bundle = vault.read("kirana", "expand into market 3")
    assert bundle.used_paths[0] == PROFILE_NOTE             # identity always first
    assert any("company profile" in n for n in bundle.notes)
    decision_paths = [p for p in bundle.used_paths if p != PROFILE_NOTE]
    assert len(decision_paths) == MAX_SELECTED_NOTES        # budget untouched


def test_hydration_runs_with_stored_profile(company, decision, isolated_vault, monkeypatch):
    import backend.main as main_mod
    client = TestClient(app)
    cid = "kirana-hydrate"

    r1 = client.post("/api/analyze", json={
        "company_id": cid, "profile": company.model_dump(), "decision": decision.model_dump()})
    assert r1.status_code == 200

    captured = {}
    orig = main_mod.build_response

    async def spy(company_id, profile, decision):
        captured["profile"] = profile
        return await orig(company_id, profile, decision)

    monkeypatch.setattr(main_mod, "build_response", spy)
    r2 = client.post("/api/analyze", json={
        "company_id": cid, "profile": None, "decision": decision.model_dump()})
    assert r2.status_code == 200

    hydrated = captured["profile"]
    for f in ("company_name", "sector", "stage", "business_model", "size_band"):
        assert getattr(hydrated, f) == getattr(company, f)
    for f in ("revenue_band", "margin", "cash_position"):
        assert getattr(hydrated.financials, f) == getattr(company.financials, f)


def test_hydration_without_stored_profile_is_422(isolated_vault):
    client = TestClient(app)
    r = client.post("/api/analyze", json={
        "company_id": "ghost-co", "profile": None,
        "decision": {"question": "Should we do X?", "constraints": {}}})
    assert r.status_code == 422
    assert "No stored profile" in r.json()["detail"]
