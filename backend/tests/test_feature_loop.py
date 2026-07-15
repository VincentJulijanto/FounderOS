"""
Feature Delivery Loop tests (Track 3: Agent Society) — hermetic, mock-pinned.

The mock fixtures are call-counted so the loop is deterministic keyless:
QA round 1 fails (PII-leak high + rate-limit medium) → SWE revises → round 2
passes → release note written to the vault (type: release, excluded from
decision retrieval).
"""

import pytest
from fastapi.testclient import TestClient

from backend.consensus.feature_loop import FeatureLoop, MAX_QA_ROUNDS
from backend.agents.qa import QAEngineerAgent
from backend.models import FeedbackTheme, AgentOutput
from backend.vault.store import Vault
from backend.main import app


@pytest.fixture
def theme():
    return FeedbackTheme(
        theme="Operational risk factors not covered",
        frequency=2,
        representative_quotes=["The board didn't factor in port congestion risk"],
        priority="high",
        thesis_aligned=True,
    )


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    from backend.vault import store
    monkeypatch.setattr(store._vault, "root", tmp_path)
    return tmp_path


# ── The full released path ─────────────────────────────────────────────────────

def test_full_loop_releases_after_one_fix_cycle(theme, isolated_vault):
    result = FeatureLoop().run("kirana", theme, feedback_notes_read=3)

    assert result.status == "released"
    assert result.iterations == 2
    # Round 1 fails on the two planted issues; round 2 passes the revised spec.
    assert [r.verdict for r in result.qa_rounds] == ["fail", "pass"]
    assert len(result.qa_rounds[0].issues) == 2
    assert {i.category for i in result.qa_rounds[0].issues} == {"leak", "bug"}
    assert result.qa_rounds[1].issues == []

    # Dialogue order: analyst gate → SWE → QA → SWE (revision) → QA.
    agents = [t.agent for t in result.loop_dialogue]
    assert agents == ["feedback_analyst", "senior_swe", "qa_engineer", "senior_swe", "qa_engineer"]
    # QA's failing turn carries its objections as challenges (auditable).
    assert result.loop_dialogue[2].challenges

    # The final spec is the revision — the leak fix is in it.
    assert result.build_spec is not None
    assert any("no verbatim" in s.lower() or "anonymised" in s.lower()
               for s in result.build_spec.security_considerations)


def test_release_note_written_and_excluded_from_decision_retrieval(theme, isolated_vault):
    result = FeatureLoop().run("kirana", theme, feedback_notes_read=3)
    assert result.release_note_path.startswith("release-")

    v = Vault(root=str(isolated_vault))
    raw = (isolated_vault / "kirana" / result.release_note_path).read_text(encoding="utf-8")
    assert "type: release" in raw
    assert result.build_spec.feature_name in raw

    # Release notes are provenance, not board memory: never in decision retrieval.
    assert v.index("kirana") == []
    bundle = v.read("kirana", theme.theme)
    assert result.release_note_path not in bundle.used_paths


# ── The gate ───────────────────────────────────────────────────────────────────

def test_single_report_is_insufficient_signal(isolated_vault):
    lone = FeedbackTheme(theme="One user's pet request", frequency=1, thesis_aligned=True)
    result = FeatureLoop().run("kirana", lone, feedback_notes_read=3)

    assert result.status == "insufficient_signal"
    assert result.gate.sufficient is False
    assert result.build_spec is None
    assert result.qa_rounds == []
    # Only the analyst spoke — no build effort was spent.
    assert [t.agent for t in result.loop_dialogue] == ["feedback_analyst"]


def test_off_thesis_theme_never_passes_the_gate(isolated_vault):
    off = FeedbackTheme(theme="Recommend a TMS vendor", frequency=5, thesis_aligned=False)
    result = FeatureLoop().run("kirana", off, feedback_notes_read=5)
    assert result.status == "insufficient_signal"
    assert "mandate" in result.gate.rationale


# ── The held path (QA never passes) ────────────────────────────────────────────

def test_loop_holds_at_round_cap_when_qa_keeps_failing(theme, isolated_vault, monkeypatch):
    def always_fail(self, profile, context={}):
        return AgentOutput(
            agent_name=self.name, role=self.role,
            analysis="Still failing.",
            raw_data={"verdict": "fail", "issues": [{
                "severity": "high", "category": "breach",
                "description": "Unresolved breach vector.", "location": "spec",
            }]},
        )

    monkeypatch.setattr(QAEngineerAgent, "analyze", always_fail)
    result = FeatureLoop().run("kirana", theme, feedback_notes_read=3)

    assert result.status == "held"
    assert result.iterations == MAX_QA_ROUNDS
    assert all(r.verdict == "fail" for r in result.qa_rounds)
    # The open issues stay on the record; nothing was released.
    assert result.qa_rounds[-1].issues
    assert result.release_note_path == ""
    assert not list((isolated_vault / "kirana").glob("release-*.md")) \
        if (isolated_vault / "kirana").exists() else True


# ── HTTP ───────────────────────────────────────────────────────────────────────

def test_feature_loop_endpoint_round_trip(theme, isolated_vault):
    client = TestClient(app)
    r = client.post("/api/feature-loop", json={
        "company_id": "harborline-logistics",
        "theme": theme.model_dump(),
        "feedback_notes_read": 3,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "released"
    assert body["mock_mode"] is True
    assert len(body["loop_dialogue"]) == 5
    assert body["release_note_path"].startswith("release-")


def test_feature_loop_rejects_bad_company_id(theme):
    client = TestClient(app)
    r = client.post("/api/feature-loop", json={
        "company_id": "../../.env",
        "theme": theme.model_dump(),
    })
    assert r.status_code == 422
