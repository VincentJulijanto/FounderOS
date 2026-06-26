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

    return VentureRecommendation(
        user_profile=profile,
        agent_outputs=list(state["agent_outputs"].values()),
        debate_rounds=state.get("debate_rounds", []),
        debate_summary=state.get("debate_summary", ""),
        consensus=state.get("consensus"),
        top_ideas=top_ideas,
        recommended_idea=top_ideas[0] if top_ideas else None,
        execution_plan=state.get("execution_plan"),
        final_memo=state.get("final_memo", ""),
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
        recommendation = await build_recommendation(request.profile)

        # Persist in memory store
        recommendations_store[recommendation.recommendation_id] = (
            recommendation.model_dump()
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

    # Update in memory store (in production: update DB)
    rec["outcome"] = request.outcome
    rec["user_feedback"] = request.notes
    recommendations_store[request.recommendation_id] = rec

    return {
        "status": "ok",
        "message": "Feedback recorded. Memory will improve future recommendations.",
    }


@app.get("/api/memory/{user_id}")
def get_memory(user_id: str):
    """
    Get a user's memory summary (episodic + semantic).
    In production, this reads from PostgreSQL.
    """
    # Filter recommendations for this user (hackathon version)
    user_recs = [
        {
            "recommendation_id": rid,
            "idea": r.get("recommended_idea", {}).get("name", "Unknown"),
            "score": r.get("recommended_idea", {}).get("startup_score", 0),
            "outcome": r.get("outcome", "pending"),
        }
        for rid, r in recommendations_store.items()
        if r.get("user_profile", {}).get("user_id") == user_id
    ]

    return {
        "user_id": user_id,
        "session_count": len(user_recs),
        "history": user_recs,
        "note": "Connect PostgreSQL for full episodic + semantic memory.",
    }


# ─────────────────────────────────────────────
# Run directly: python -m backend.main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
