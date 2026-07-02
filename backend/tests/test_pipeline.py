"""
Smoke tests for the FounderOS board pipeline in mock mode.
Run with: pytest backend/tests/test_pipeline.py -v
No API key required — USE_MOCK_LLM=true by default.

Fixtures `company`, `decision`, `decision_no_options` live in conftest.py.
"""

import json
import pytest

from backend.models import BoardResponse, BoardRecommendation
from backend.main import run_board


# ── Board memo shape ──────────────────────────────────────────────────────────

def test_response_has_required_fields(company, decision):
    resp = run_board("kirana-logistics", company, decision)
    assert isinstance(resp, BoardResponse)
    assert resp.response_id
    assert resp.company_id == "kirana-logistics"
    assert isinstance(resp.agent_outputs, list)
    assert isinstance(resp.debate_rounds, list)
    assert isinstance(resp.recommendation, BoardRecommendation)


def test_recommendation_is_well_formed(company, decision):
    rec = run_board("kirana-logistics", company, decision).recommendation
    assert rec.recommendation in ("proceed", "hold", "conditional")
    assert rec.confidence in ("low", "medium", "high")
    assert rec.rationale
    assert rec.disclaimer
    # Trust posture — the memo never pretends completeness.
    assert isinstance(rec.missing_inputs, list) and rec.missing_inputs
    assert rec.what_would_change_this_call


def test_options_assessed_map_one_to_one(company, decision):
    """Every option on the table gets an assessment (1:1)."""
    rec = run_board("kirana-logistics", company, decision).recommendation
    assessed = {a.option for a in rec.options_assessed}
    for opt in decision.options:
        assert opt in assessed


def test_options_assessed_one_to_one_on_count_mismatch(company, decision):
    """1:1 holds even when the operator's option count differs from the
    Chair's (the mock fixture always returns three): exactly one assessment
    per operator option, under the operator's own strings — no fixture-labelled
    extras, no 'Not separately assessed.' stubs."""
    decision.options = decision.options[:2]  # 2 options vs the fixture's 3
    rec = run_board("kirana-logistics", company, decision).recommendation
    assert [a.option for a in rec.options_assessed] == decision.options
    for a in rec.options_assessed:
        assert a.assessment
        assert "not separately assessed" not in a.assessment.lower()


def test_execution_plan_is_phased(company, decision):
    rec = run_board("kirana-logistics", company, decision).recommendation
    phases = rec.execution_plan.phases
    assert len(phases) >= 2
    assert all(p.name and p.objective for p in phases)
    assert any(p.actions for p in phases)


def test_scout_frames_options_when_empty(company, decision_no_options):
    """With no options supplied, the board still assesses framed alternatives."""
    resp = run_board("kirana-logistics", company, decision_no_options)
    assert resp.recommendation.options_assessed  # Scout framed something to assess


# ── Agent society shape ───────────────────────────────────────────────────────

def test_all_seven_agents_appear_in_output(company, decision):
    resp = run_board("kirana-logistics", company, decision)
    names = {o.agent_name for o in resp.agent_outputs}
    expected = {
        "scout", "trend", "finance", "growth",
        "skeptic", "capability", "venture_partner",
    }
    assert expected == names, f"Missing or extra agents: {expected ^ names}"


# ── Debate & consensus engine ─────────────────────────────────────────────────

import pytest  # noqa: E402
from backend.consensus import debate_engine
from backend.consensus.debate_engine import DebateEngine


def test_debate_runs_in_mock(company, decision):
    """Mock produces a representative negotiation — debate is exercised keyless."""
    resp = run_board("kirana-logistics", company, decision)
    assert len(resp.debate_rounds) == 2          # 2-round fixture
    assert resp.consensus is not None


def test_conflict_parsing():
    """Detector parses the three fixture conflicts with correct severities/parties."""
    conflicts, has_conflicts, summary = DebateEngine().detect_conflicts({})
    assert has_conflicts is True
    assert summary
    assert len(conflicts) == 3
    topics = {c.topic for c in conflicts}
    assert "Capital commitment vs reversibility" in topics
    severities = sorted(c.severity for c in conflicts)
    assert severities == ["high", "low", "medium"]
    # Two conflicts involve the Skeptic (demand durability, timeline).
    skeptic_involved = [
        c for c in conflicts
        if "skeptic" in c.agent_a.lower() or "skeptic" in c.agent_b.lower()
    ]
    assert len(skeptic_involved) == 2


def test_per_round_subset():
    """Each round debates only the conflicts still open — round 2 ⊂ round 1."""
    rounds, _ = DebateEngine().run_debate(
        {}, DebateEngine().detect_conflicts({})[0], "ctx"
    )
    assert len(rounds) == 2
    r1_topics = {c.topic for c in rounds[0].conflicts_identified}
    r2_topics = {c.topic for c in rounds[1].conflicts_identified}
    assert len(r1_topics) == 3
    assert r2_topics == {"Durability of anchor demand"}
    assert r2_topics < r1_topics


def test_consensus_score_value():
    """The worked example: 4.5 / 7.5 → 6.0, Moderate, 1 unresolved (medium, Skeptic)."""
    _, report = DebateEngine().run({}, "ctx")
    assert report.consensus_score == 6.0
    assert report.label == "Moderate consensus"
    assert report.total_conflicts == 3
    assert report.resolved_conflicts == 2
    assert len(report.unresolved_conflicts) == 1
    unresolved = report.unresolved_conflicts[0]
    assert unresolved.topic == "Durability of anchor demand"
    assert unresolved.severity == "medium"
    assert unresolved.resolved is False
    assert "skeptic" in (unresolved.agent_a + unresolved.agent_b).lower()


def test_consensus_no_conflicts(monkeypatch):
    """No conflicts detected → full consensus, score 10.0, zero rounds."""
    monkeypatch.setattr(debate_engine, "_MOCK_CONFLICTS", json.dumps({
        "conflicts": [],
        "has_significant_conflicts": False,
        "conflict_summary": "Board aligned.",
    }))
    rounds, report = DebateEngine().run({}, "ctx")
    assert rounds == []
    assert report.consensus_score == 10.0
    assert report.label == "Full consensus (no conflicts)"
    assert report.total_conflicts == 0
    assert report.rounds_used == 0


# ── Dissent record derives from unresolved conflicts ──────────────────────────

def test_dissent_reflects_unresolved_conflict(company, decision):
    """The memo's dissent record carries the debate's unresolved objection."""
    rec = run_board("kirana-logistics", company, decision).recommendation
    assert rec.dissent  # at least the unresolved anchor-demand objection
    # The unresolved conflict is skeptic-held in the fixture.
    assert any("skeptic" in d.agent.lower() for d in rec.dissent)


# ── Determinism in mock mode ──────────────────────────────────────────────────

def test_two_runs_same_inputs_same_recommendation(company, decision):
    a = run_board("kirana-logistics", company, decision).recommendation
    b = run_board("kirana-logistics", company, decision).recommendation
    assert a.recommendation == b.recommendation


# ── LangGraph orchestration ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_graph_state_has_expected_keys(company, decision):
    from backend.graph import run_graph

    state = await run_graph(company, decision)

    for key in ("company_profile", "decision", "agent_outputs",
                "debate_rounds", "recommendation", "errors"):
        assert key in state, f"missing state key: {key}"

    assert len(state["agent_outputs"]) == 7
    assert state["errors"] == []
    assert state["recommendation"] is not None
