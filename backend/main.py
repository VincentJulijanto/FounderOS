"""
FounderOS — FastAPI Backend Entry Point

Endpoints:
  POST /api/analyze          — Submit founder profile, receive full recommendation
  GET  /api/recommendation/{id} — Fetch a saved recommendation
  POST /api/feedback         — Submit outcome feedback (updates memory)
  GET  /api/memory/{user_id} — Get user's memory summary
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from .config import settings
from .models import (
    AnalyzeRequest,
    FeedbackRequest,
    VentureRecommendation,
)
from .graph import run_graph
from .memory import memory_store

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="FounderOS API",
    description="AI Venture Studio — Agent Society Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for hackathon (swap with PostgreSQL for production)
recommendations_store: dict[str, dict] = {}


# ─────────────────────────────────────────────
# Core Orchestration
# ─────────────────────────────────────────────

async def build_recommendation(profile, memory_context: str = "") -> VentureRecommendation:
    """
    Run the LangGraph agent society and assemble the API response.
    Pipeline (see backend/graph.py):
    Scout → Trend ∥ Finance ∥ Growth (parallel fan-out) → Skeptic → Founder-Fit → Debate → Venture Partner
    """
    state = await run_graph(profile, memory_context)
    top_ideas = state.get("top_ideas", [])
    agent_outputs = list(state["agent_outputs"].values())

    # MCP (Phase 6) — collect the provenance every agent attached to its output.
    # mock sources are prefixed "[MOCK] "; any non-mock source means live data ran.
    mcp_sources: list[str] = []
    for out in agent_outputs:
        mcp_sources.extend(out.raw_data.get("mcp_sources", []))
    mcp_sources = list(dict.fromkeys(mcp_sources))  # dedupe, order-preserving
    mcp_used = any(not s.startswith("[MOCK] ") for s in mcp_sources)

    return VentureRecommendation(
        user_profile=profile,
        agent_outputs=agent_outputs,
        debate_rounds=state.get("debate_rounds", []),
        debate_summary=state.get("debate_summary", ""),
        consensus=state.get("consensus"),
        top_ideas=top_ideas,
        recommended_idea=top_ideas[0] if top_ideas else None,
        execution_plan=state.get("execution_plan"),
        final_memo=state.get("final_memo", ""),
        mcp_used=mcp_used,
        mcp_sources=mcp_sources,
    )


def run_agent_society(profile, memory_context: str = "") -> VentureRecommendation:
    """Synchronous wrapper around the async graph — used by tests and any sync caller."""
    return asyncio.run(build_recommendation(profile, memory_context))


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "FounderOS API is running",
        "version": "1.0.0",
        "llm_mode": "live" if settings.is_live else "mock",
        "model": settings.qwen_model if settings.is_live else "mock-fixture",
        "tip": None if settings.is_live else "Set QWEN_API_KEY and USE_MOCK_LLM=false in .env to go live.",
    }


@app.post("/api/analyze", response_model=VentureRecommendation)
async def analyze(request: AnalyzeRequest):
    """
    Submit a founder profile and receive a full venture recommendation.
    This is the main endpoint — runs the full agent society pipeline (LangGraph).
    """
    try:
        profile = request.profile

        # Memory loop (Phase 5) — load this founder's prior sessions + learned
        # insights and feed them to the agent society (the VP folds them into its
        # synthesis). Empty string for a first-time founder.
        memory_context = memory_store.build_context(profile.user_id)

        recommendation = await build_recommendation(profile, memory_context)

        # Persist in the request store (kept for /api/recommendation/{id})
        recommendations_store[recommendation.recommendation_id] = (
            recommendation.model_dump()
        )

        # Record this session as an episodic memory so the next analysis can learn.
        rec_idea = recommendation.recommended_idea
        memory_store.record_session(
            user_id=profile.user_id,
            recommendation_id=recommendation.recommendation_id,
            recommended_idea=rec_idea.name if rec_idea else "Unknown",
            startup_score=rec_idea.startup_score if rec_idea else 0.0,
            top_idea_names=[i.name for i in recommendation.top_ideas],
        )

        return recommendation

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent pipeline failed: {str(e)}")


@app.get("/api/recommendation/{recommendation_id}")
def get_recommendation(recommendation_id: str):
    """Fetch a previously generated recommendation."""
    rec = recommendations_store.get(recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):
    """
    Submit outcome feedback for a recommendation.
    Updates episodic memory (in production, writes to PostgreSQL).
    """
    rec = recommendations_store.get(request.recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    # Update the request store snapshot.
    rec["outcome"] = request.outcome
    rec["user_feedback"] = request.notes
    recommendations_store[request.recommendation_id] = rec

    # Memory loop (Phase 5) — record the real outcome and re-derive semantic
    # insights so the next analysis for this founder learns from it.
    user_id = request.user_id or rec.get("user_profile", {}).get("user_id", "")
    memory_store.update_outcome(
        user_id=user_id,
        recommendation_id=request.recommendation_id,
        outcome=request.outcome,
        feedback=request.notes,
    )

    return {
        "status": "ok",
        "message": "Feedback recorded. Memory will improve future recommendations.",
        "insights": memory_store.format_semantic(user_id),
    }


@app.get("/api/memory/{user_id}")
def get_memory(user_id: str):
    """
    Get a user's memory summary — real episodic history + learned semantic insights
    from the in-process Memory Loop (Phase 5). Swap memory_store for the Postgres
    services in production.
    """
    summary = memory_store.summary(user_id)
    summary["note"] = "Connect PostgreSQL (EpisodicMemory/SemanticMemory) for durable memory."
    return summary


# ─────────────────────────────────────────────
# Run directly: python -m backend.main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
