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
import json

from .config import settings
from .models import (
    AnalyzeRequest,
    FeedbackRequest,
    VentureRecommendation,
    AgentOutput,
)
from .agents import (
    OpportunityScoutAgent,
    TrendAnalystAgent,
    FinanceAgent,
    SkepticAgent,
    GrowthAgent,
    VenturePartnerAgent,
)
from .consensus.debate_engine import DebateEngine

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

def run_agent_society(profile, memory_context: str = "") -> VentureRecommendation:
    """
    Orchestrate the full agent society pipeline:
    Scout → Trend + Finance + Growth (parallel) → Skeptic → Debate → Venture Partner
    """

    # --- Step 1: Scout opportunities ---
    scout = OpportunityScoutAgent()
    scout_output = scout.analyze(profile)
    opportunities = scout_output.raw_data.get("opportunities", [])

    context = {"opportunities": opportunities}

    # --- Step 2: Parallel analysis (Trend, Finance, Growth) ---
    trend = TrendAnalystAgent()
    finance = FinanceAgent()
    growth = GrowthAgent()

    trend_output = trend.analyze(profile, context)
    finance_output = finance.analyze(profile, context)
    growth_output = growth.analyze(profile, context)

    # Pass financial data to skeptic for reality-checking
    finance_context = finance_output.raw_data.get("financial_analysis", [])
    market_context = trend_output.raw_data.get("market_analysis", [])

    # --- Step 3: Skeptic challenges everything ---
    skeptic = SkepticAgent()
    skeptic_output = skeptic.analyze(
        profile,
        {
            **context,
            "financial_analysis": finance_context,
            "market_analysis": market_context,
        },
    )

    # --- Step 4: Debate Engine ---
    all_outputs: dict[str, AgentOutput] = {
        "Opportunity Scout": scout_output,
        "Trend Analyst": trend_output,
        "Finance Agent": finance_output,
        "Growth Agent": growth_output,
        "Skeptic Agent": skeptic_output,
    }

    debate_engine = DebateEngine()
    profile_context = (
        f"Founder: {profile.name}, Budget: SGD {profile.budget}, "
        f"Hours/week: {profile.weekly_hours}, Goals: {profile.goals}\n"
        f"Memory context:\n{memory_context}"
    )
    debate_rounds, debate_summary = debate_engine.run(all_outputs, profile_context)

    # --- Step 5: Venture Partner makes final call ---
    vp = VenturePartnerAgent()
    vp_context = {
        "scout_output": scout_output,
        "trend_output": trend_output,
        "finance_output": finance_output,
        "growth_output": growth_output,
        "skeptic_output": skeptic_output,
        "debate_summary": debate_summary,
        "memory_context": memory_context,
    }
    vp_output = vp.analyze(profile, vp_context)

    top_ideas, execution_plan = vp.build_structured_recommendation(
        vp_output.raw_data, profile
    )

    return VentureRecommendation(
        user_profile=profile,
        agent_outputs=list(all_outputs.values()) + [vp_output],
        debate_rounds=debate_rounds,
        top_ideas=top_ideas,
        recommended_idea=top_ideas[0] if top_ideas else None,
        execution_plan=execution_plan,
        final_memo=vp_output.analysis,
    )


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "FounderOS API is running 🚀", "version": "1.0.0"}


@app.post("/api/analyze", response_model=VentureRecommendation)
def analyze(request: AnalyzeRequest):
    """
    Submit a founder profile and receive a full venture recommendation.
    This is the main endpoint — runs the full agent society pipeline.
    """
    try:
        recommendation = run_agent_society(request.profile)

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
