"""
Phase 5 — Memory Loop tests (mock mode, no Postgres, no API key).

Covers the full loop: analyze → record episode → feedback → learn semantic
insights → next analyze receives that memory → the Venture Partner prompt
actually uses it.
"""

import json

import pytest
from fastapi.testclient import TestClient

from backend.memory import memory_store, MemoryStore
from backend.memory.store import Episode
from backend.models import UserProfile
from backend.main import app, run_agent_society
from backend.agents import VenturePartnerAgent


@pytest.fixture(autouse=True)
def clean_memory():
    """Every test starts with an empty store, and leaves it empty."""
    memory_store.reset()
    yield
    memory_store.reset()


@pytest.fixture
def founder():
    return UserProfile(
        user_id="founder-1",
        name="Alex Tan",
        background="NUS CS student",
        skills=["Python", "React"],
        budget=500,
        weekly_hours=10,
        interests=["AI", "education"],
        goals="SGD 2,000/month side income",
    )


# ── Episodic store ────────────────────────────────────────────────────────────

def test_new_user_has_empty_context():
    store = MemoryStore()
    assert store.build_context("nobody") == ""
    assert store.format_episodic("nobody") == "No previous sessions found."
    assert store.format_semantic("nobody") == "No semantic insights yet."


def test_record_session_appears_in_history():
    store = MemoryStore()
    store.record_session("u1", "rec-1", "AI Tutor", 7.5, ["AI Tutor", "Note Bot"])
    history = store.get_history("u1")
    assert len(history) == 1
    assert history[0].recommended_idea == "AI Tutor"
    assert "AI Tutor" in store.build_context("u1")


def test_update_outcome_unknown_recommendation_returns_false():
    store = MemoryStore()
    assert store.update_outcome("u1", "missing", "launched") is False


def test_update_outcome_sets_outcome_and_feedback():
    store = MemoryStore()
    store.record_session("u1", "rec-1", "AI Tutor", 7.5)
    assert store.update_outcome("u1", "rec-1", "launched", "shipped it") is True
    e = store.get_history("u1")[0]
    assert e.outcome == "launched"
    assert e.feedback == "shipped it"


def test_history_most_recent_first_and_limited():
    store = MemoryStore()
    for i in range(7):
        store.record_session("u1", f"rec-{i}", f"Idea {i}", 5.0)
    history = store.get_history("u1", limit=3)
    assert [e.recommended_idea for e in history] == ["Idea 6", "Idea 5", "Idea 4"]


# ── Semantic insight extraction (heuristic, keyless) ──────────────────────────

def test_two_abandonments_produce_constraint_insight():
    store = MemoryStore()
    store.record_session("u1", "r1", "Service A", 6.0)
    store.record_session("u1", "r2", "Service B", 6.5)
    store.update_outcome("u1", "r1", "abandoned")
    store.update_outcome("u1", "r2", "abandoned")

    insights = {i.key: i for i in store.get_insights("u1")}
    assert "abandonment_pattern" in insights
    assert insights["abandonment_pattern"].insight_type == "constraint"
    assert "abandoned 2" in insights["abandonment_pattern"].value


def test_two_launches_produce_track_record_insight():
    store = MemoryStore()
    store.record_session("u1", "r1", "Product A", 8.0)
    store.record_session("u1", "r2", "Product B", 8.5)
    store.update_outcome("u1", "r1", "launched")
    store.update_outcome("u1", "r2", "launched")

    insights = {i.key: i for i in store.get_insights("u1")}
    assert "execution_track_record" in insights
    assert insights["execution_track_record"].insight_type == "pattern"


def test_recurring_theme_detected():
    store = MemoryStore()
    store.record_session("u1", "r1", "Study Buddy", 7.0)
    store.record_session("u1", "r2", "Study Planner", 7.0)
    store.update_outcome("u1", "r1", "abandoned")  # triggers extraction

    insights = {i.key: i for i in store.get_insights("u1")}
    assert "recurring_theme" in insights
    assert "study" in insights["recurring_theme"].value.lower()


def test_score_baseline_insight_after_two_sessions():
    store = MemoryStore()
    store.record_session("u1", "r1", "Idea A", 6.0)
    store.record_session("u1", "r2", "Idea B", 8.0)
    store.update_outcome("u1", "r1", "in_progress")

    insights = {i.key: i for i in store.get_insights("u1")}
    assert "historical_score_baseline" in insights
    assert "7.0/10" in insights["historical_score_baseline"].value


def test_single_session_yields_no_speculative_insights():
    store = MemoryStore()
    store.record_session("u1", "r1", "Idea A", 6.0)
    store.update_outcome("u1", "r1", "abandoned")
    assert store.get_insights("u1") == []  # one data point — no patterns


# ── Venture Partner actually consumes memory_context (mandatory Phase 5 fix) ───

def test_vp_prompt_includes_memory_context(founder, monkeypatch):
    captured = {}

    def fake_call_llm(self, system, user, max_tokens=2000):
        captured["system"] = system
        captured["user"] = user
        return self._mock_response()

    monkeypatch.setattr(VenturePartnerAgent, "_call_llm", fake_call_llm)

    memory_ctx = "PAST SESSIONS (episodic):\n- Abandoned 'AI Tutor'."
    VenturePartnerAgent().analyze(founder, {"memory_context": memory_ctx})

    assert memory_ctx in captured["user"], "VP prompt must embed memory_context"
    assert "Founder Memory" in captured["user"]
    # System prompt now instructs the VP to weigh memory.
    assert "MEMORY" in captured["system"]


def test_vp_prompt_handles_empty_memory(founder, monkeypatch):
    captured = {}

    def fake_call_llm(self, system, user, max_tokens=2000):
        captured["user"] = user
        return self._mock_response()

    monkeypatch.setattr(VenturePartnerAgent, "_call_llm", fake_call_llm)
    VenturePartnerAgent().analyze(founder, {})  # no memory_context key
    assert "first session" in captured["user"].lower()


# ── Memory OBSERVABLY changes the recommendation (item-3 deliverable, keyless) ──
# The prompt-level tests above prove memory reaches the VP. These prove it changes
# the OUTPUT: same founder, empty vs seeded memory → different recommendation
# CONTENT, not just an echoed memory string. This is the real keyless proof.


def _seeded_abandonment_context() -> str:
    """A realistic memory_context block for a founder who abandoned 2 ventures."""
    store = MemoryStore()
    store.record_session("u", "r1", "AI Tutor", 6.0)
    store.record_session("u", "r2", "AI Study Coach", 6.5)
    store.update_outcome("u", "r1", "abandoned")
    store.update_outcome("u", "r2", "abandoned")
    return store.build_context("u")


def test_vp_output_shifts_when_memory_has_abandonment(founder):
    vp = VenturePartnerAgent()
    no_mem = vp.analyze(founder, {}).raw_data
    seeded = vp.analyze(
        founder, {"memory_context": _seeded_abandonment_context()}
    ).raw_data

    # Ranking shifts: the #1 pick moves away from the abandoned AI-tutor direction.
    assert no_mem["top_ideas"][0]["name"] == "AI Study Buddy"
    assert seeded["top_ideas"][0]["name"] != no_mem["top_ideas"][0]["name"]

    # Meaningful fields differ — memo + execution plan, not just a timestamp.
    assert seeded["final_memo"] != no_mem["final_memo"]
    assert (
        seeded["execution_plan"]["startup_name"]
        != no_mem["execution_plan"]["startup_name"]
    )

    # And it reflects the SPECIFIC abandoned ideas, not a generic echo.
    assert "AI Tutor" in seeded["final_memo"]
    assert seeded.get("memory_informed") is True


def test_vp_output_byte_identical_for_empty_memory(founder):
    """Guard: with no memory the output is unchanged, so any diff above is the
    memory loop's doing and nothing else."""
    vp = VenturePartnerAgent()
    a = vp.analyze(founder, {}).raw_data
    b = vp.analyze(founder, {"memory_context": ""}).raw_data
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_agent_output_recommendations_reflect_memory(founder):
    """The AgentOutput surface (what the graph/API consume) reflects the shift too."""
    vp = VenturePartnerAgent()
    no_mem = vp.analyze(founder, {})
    seeded = vp.analyze(founder, {"memory_context": _seeded_abandonment_context()})

    assert no_mem.recommendations[0] != seeded.recommendations[0]
    assert no_mem.analysis != seeded.analysis  # final_memo surfaced as analysis


# ── End-to-end through the HTTP API ───────────────────────────────────────────

def test_analyze_then_feedback_then_memory_endpoint(founder):
    client = TestClient(app)
    payload = {"profile": founder.model_dump()}

    # Session 1
    r1 = client.post("/api/analyze", json=payload)
    assert r1.status_code == 200
    rec_id = r1.json()["recommendation_id"]

    # Memory endpoint now reflects the session
    mem = client.get(f"/api/memory/{founder.user_id}").json()
    assert mem["session_count"] == 1
    assert mem["history"][0]["outcome"] == "pending"

    # Feedback — abandoned
    fb = client.post("/api/feedback", json={
        "recommendation_id": rec_id,
        "user_id": founder.user_id,
        "outcome": "abandoned",
        "notes": "lost interest",
    })
    assert fb.status_code == 200

    mem2 = client.get(f"/api/memory/{founder.user_id}").json()
    assert mem2["history"][0]["outcome"] == "abandoned"


def test_memory_context_grows_across_sessions(founder):
    """Two analyses + two abandonments must yield a learned constraint insight."""
    client = TestClient(app)
    payload = {"profile": founder.model_dump()}

    for _ in range(2):
        rec_id = client.post("/api/analyze", json=payload).json()["recommendation_id"]
        client.post("/api/feedback", json={
            "recommendation_id": rec_id,
            "user_id": founder.user_id,
            "outcome": "abandoned",
            "notes": "no",
        })

    # Context fed to the next analysis carries both episodic + semantic memory.
    ctx = memory_store.build_context(founder.user_id)
    assert "PAST SESSIONS" in ctx
    assert "LEARNED INSIGHTS" in ctx
    assert "abandoned 2" in ctx

    mem = client.get(f"/api/memory/{founder.user_id}").json()
    keys = {i["key"] for i in mem["semantic_insights"]}
    assert "abandonment_pattern" in keys


def test_feedback_unknown_recommendation_404(founder):
    client = TestClient(app)
    resp = client.post("/api/feedback", json={
        "recommendation_id": "does-not-exist",
        "user_id": founder.user_id,
        "outcome": "launched",
    })
    assert resp.status_code == 404


def test_two_users_memory_is_isolated():
    store = MemoryStore()
    store.record_session("a", "r1", "Idea A", 7.0)
    store.record_session("b", "r2", "Idea B", 6.0)
    assert store.summary("a")["session_count"] == 1
    assert "Idea A" in store.build_context("a")
    assert "Idea A" not in store.build_context("b")
