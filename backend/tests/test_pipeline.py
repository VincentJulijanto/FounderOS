"""
Smoke tests for the FounderOS agent pipeline in mock mode.
Run with: pytest backend/tests/test_pipeline.py -v
No API key required — USE_MOCK_LLM=true by default.
"""

import pytest
from backend.models import UserProfile, VentureRecommendation
from backend.main import run_agent_society


@pytest.fixture
def cs_founder():
    return UserProfile(
        name="Alex Tan",
        background="NUS Computer Science student, Year 2",
        skills=["Python", "React", "machine learning"],
        budget=500,
        weekly_hours=10,
        interests=["AI", "education", "productivity"],
        goals="Earn SGD 2,000/month side income within 3 months",
    )


@pytest.fixture
def design_founder():
    return UserProfile(
        name="Priya Sharma",
        background="Graphic designer with 2 years freelance experience",
        skills=["Figma", "brand design", "social media"],
        budget=200,
        weekly_hours=8,
        interests=["sustainability", "e-commerce", "wellness"],
        goals="Replace full-time salary with freelance + product income",
    )


# ── Schema completeness ───────────────────────────────────────────────────────

def test_recommendation_has_required_fields(cs_founder):
    rec = run_agent_society(cs_founder)
    assert rec.recommendation_id
    assert rec.user_profile.name == "Alex Tan"
    assert isinstance(rec.agent_outputs, list)
    assert isinstance(rec.debate_rounds, list)
    assert isinstance(rec.top_ideas, list)
    assert rec.recommended_idea is not None
    assert rec.execution_plan is not None
    assert rec.final_memo


def test_top_idea_scores_in_range(cs_founder):
    rec = run_agent_society(cs_founder)
    idea = rec.top_ideas[0]
    assert idea.name
    assert 0 <= idea.startup_score <= 10
    assert 0 <= idea.feasibility_score <= 10
    assert 0 <= idea.market_attractiveness_score <= 10
    assert 0 <= idea.founder_fit_score <= 10
    assert 0 <= idea.risk_score <= 10
    assert idea.risk_level in ("Low", "Medium", "High")


def test_execution_plan_is_complete(cs_founder):
    rec = run_agent_society(cs_founder)
    plan = rec.execution_plan
    assert plan.startup_name
    assert plan.value_proposition
    assert plan.customer_persona
    assert plan.lean_canvas.problem
    assert plan.lean_canvas.solution
    assert plan.lean_canvas.revenue_streams
    assert plan.mvp_scope
    assert plan.elevator_pitch
    assert len(plan.thirty_day_roadmap) >= 4


def test_outreach_templates_present(cs_founder):
    rec = run_agent_society(cs_founder)
    templates = rec.execution_plan.customer_outreach_templates
    assert "cold_email" in templates
    assert "linkedin_dm" in templates


# ── Agent society shape ───────────────────────────────────────────────────────

def test_all_seven_agents_appear_in_output(cs_founder):
    rec = run_agent_society(cs_founder)
    names = {o.agent_name for o in rec.agent_outputs}
    expected = {
        "Opportunity Scout", "Trend Analyst", "Finance Agent",
        "Growth Agent", "Skeptic Agent", "Founder-Fit Agent", "Venture Partner",
    }
    assert expected == names, f"Missing or extra agents: {expected ^ names}"


# ── Debate & consensus engine (Phase 4) ──────────────────────────────────────

import json
import pytest
from backend.consensus import debate_engine
from backend.consensus.debate_engine import DebateEngine


def test_debate_runs_in_mock(cs_founder):
    """Mock now produces a representative negotiation — debate is exercised keyless."""
    rec = run_agent_society(cs_founder)
    assert len(rec.debate_rounds) == 2          # 2-round fixture
    assert rec.consensus is not None
    assert rec.debate_summary == rec.consensus.summary  # mirrored, not divergent


def test_conflict_parsing():
    """Detector parses the three fixture conflicts with correct severities/parties."""
    conflicts, has_conflicts, summary = DebateEngine().detect_conflicts({})
    assert has_conflicts is True
    assert summary                                # conflict_summary surfaced
    assert len(conflicts) == 3
    topics = {c.topic for c in conflicts}
    assert "Paid acquisition vs zero ad budget" in topics
    severities = sorted(c.severity for c in conflicts)
    assert severities == ["high", "low", "medium"]
    # Two conflicts involve the Skeptic (willingness-to-pay, timeline).
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
    assert r2_topics == {"Willingness to pay"}    # only the unresolved one carries forward
    assert r2_topics < r1_topics


def test_early_resolution_break(monkeypatch):
    """If a round resolves everything, the loop stops there (no spinning)."""
    all_resolved = json.dumps({
        "debate_exchanges": [
            {"conflict_topic": "Paid acquisition vs zero ad budget", "resolved": True,
             "agent_a_rebuttal": "", "agent_b_rebuttal": "", "moderator_verdict": ""},
            {"conflict_topic": "Willingness to pay", "resolved": True,
             "agent_a_rebuttal": "", "agent_b_rebuttal": "", "moderator_verdict": ""},
            {"conflict_topic": "Launch timeline realism", "resolved": True,
             "agent_a_rebuttal": "", "agent_b_rebuttal": "", "moderator_verdict": ""},
        ],
        "revised_positions": {},
        "overall_resolution_achieved": True,
        "round_summary": "All conflicts resolved in one round.",
    })
    monkeypatch.setattr(debate_engine, "_MOCK_ROUNDS", [all_resolved])

    rounds, report = DebateEngine().run(({}), "ctx")
    assert len(rounds) == 1
    assert report.consensus_score == 10.0
    assert report.resolved_conflicts == 3
    assert report.unresolved_conflicts == []


def test_consensus_score_value():
    """The worked example: 4.5 / 7.5 → 6.0, Moderate, 1 unresolved (medium, Skeptic)."""
    _, report = DebateEngine().run({}, "ctx")
    assert report.consensus_score == 6.0
    assert report.label == "Moderate consensus"
    assert report.total_conflicts == 3
    assert report.resolved_conflicts == 2
    assert len(report.unresolved_conflicts) == 1
    unresolved = report.unresolved_conflicts[0]
    assert unresolved.topic == "Willingness to pay"
    assert unresolved.severity == "medium"
    assert unresolved.resolved is False
    assert "skeptic" in (unresolved.agent_a + unresolved.agent_b).lower()


def test_consensus_no_conflicts(monkeypatch):
    """No conflicts detected → full consensus, score 10.0, zero rounds."""
    monkeypatch.setattr(debate_engine, "_MOCK_CONFLICTS", json.dumps({
        "conflicts": [],
        "has_significant_conflicts": False,
        "conflict_summary": "Agents aligned.",
    }))
    rounds, report = DebateEngine().run({}, "ctx")
    assert rounds == []
    assert report.consensus_score == 10.0
    assert report.label == "Full consensus (no conflicts)"
    assert report.total_conflicts == 0
    assert report.rounds_used == 0


# ── Pipeline is deterministic in mock mode ───────────────────────────────────

def test_two_runs_same_profile_same_top_idea(cs_founder):
    rec_a = run_agent_society(cs_founder)
    rec_b = run_agent_society(cs_founder)
    assert rec_a.top_ideas[0].name == rec_b.top_ideas[0].name


# ── Different profiles both succeed ──────────────────────────────────────────

def test_design_founder_pipeline_succeeds(design_founder):
    rec = run_agent_society(design_founder)
    assert rec.recommendation_id
    assert rec.top_ideas[0].name


# ── Founder-Fit agent (Phase 2) ──────────────────────────────────────────────

def test_founder_fit_mock_returns_expected_keys(cs_founder):
    from backend.agents import FounderFitAgent

    agent = FounderFitAgent()
    data = agent._parse_json(agent._mock_response())

    # 5 dimensions, each with a numeric score and a rationale
    expected_dims = {
        "founder_background", "domain_expertise", "execution_history",
        "team_composition", "coachability",
    }
    assert set(data["dimensions"]) == expected_dims
    for dim in expected_dims:
        d = data["dimensions"][dim]
        assert isinstance(d["score"], (int, float))
        assert 0 <= d["score"] <= 10
        assert d["rationale"]

    # overall score + summary
    assert 0 <= data["overall_fit_score"] <= 10
    assert data["summary"]


def test_founder_fit_analyze_returns_structured_output(cs_founder):
    from backend.agents import FounderFitAgent

    out = FounderFitAgent().analyze(cs_founder, {"opportunities": []})
    assert out.agent_name == "Founder-Fit Agent"
    assert 0 <= out.score <= 10
    assert out.key_findings  # dimension scores surfaced as findings


# ── LangGraph orchestration (Phase 3) ────────────────────────────────────────

def test_analyst_fanout_all_three_present(cs_founder):
    """A single /api/analyze call must return all three fanned-out analysts."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.post("/api/analyze", json={"profile": cs_founder.model_dump()})
    assert resp.status_code == 200

    names = {o["agent_name"] for o in resp.json()["agent_outputs"]}
    assert {"Trend Analyst", "Finance Agent", "Growth Agent"}.issubset(names)
    assert len(names) == 7  # response shape unchanged — all 7 agents


@pytest.mark.asyncio
async def test_run_graph_state_has_expected_keys(cs_founder):
    """run_graph returns a state dict with all expected keys populated."""
    from backend.graph import run_graph

    state = await run_graph(cs_founder)

    for key in ("startup_profile", "agent_outputs", "debate_rounds",
                "top_ideas", "execution_plan", "final_memo", "errors"):
        assert key in state, f"missing state key: {key}"

    assert len(state["agent_outputs"]) == 7
    assert state["errors"] == []
    assert state["top_ideas"]  # at least one idea produced
