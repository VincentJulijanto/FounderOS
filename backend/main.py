"""
FounderOS — FastAPI Backend Entry Point (evaluator board)

Endpoints (contract in docs/architecture.md § API Architecture):
  POST /api/analyze              — Evaluate one company decision → BoardResponse
  GET  /api/response/{id}        — Fetch a saved BoardResponse
  POST /api/feedback             — Outcome loop → vault write-back
  GET  /api/company/{company_id} — The company's decision history (from the vault)
"""

import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import asyncio

logger = logging.getLogger(__name__)

from .config import settings
from .models import (
    AnalyzeRequest,
    FeedbackRequest,
    BoardResponse,
    CompanyProfile,
    Decision,
)
from .graph import run_graph
from . import vault

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

# Rate limits are env-tunable (e.g. raise ANALYZE_RATE_LIMIT on demo day, or
# set RATE_LIMIT_ENABLED=false in tests) — no code change needed.
ANALYZE_RATE_LIMIT = os.environ.get("ANALYZE_RATE_LIMIT", "5/minute")
FEEDBACK_RATE_LIMIT = os.environ.get("FEEDBACK_RATE_LIMIT", "20/minute")
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.environ.get("RATE_LIMIT_ENABLED", "true").lower() != "false",
)

app = FastAPI(
    title="FounderOS API",
    description="AI board of directors — evaluate one company decision, get a board memo",
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for the demo (the durable record is the vault). Maps
# response_id → (BoardResponse dump, company_id, Decision) so feedback can
# write the outcome back to the right vault note.
responses_store: dict[str, dict] = {}


# ─────────────────────────────────────────────
# Core Orchestration
# ─────────────────────────────────────────────

async def build_response(
    company_id: str, profile: CompanyProfile, decision: Decision
) -> tuple[BoardResponse, list[str]]:
    """
    Run the board on one decision and assemble the API response.
    Pipeline (see backend/graph.py):
    Scout → Trend ∥ Finance ∥ Growth ∥ Capability → Skeptic → Debate → Chair
    Returns the response plus the paths of the vault notes that informed the run.
    """
    # Selective retrieval — the vault picks only the notes relevant to this decision.
    bundle = vault.read(company_id, decision.question)
    vault_context = bundle.as_prompt_block()

    state = await run_graph(profile, decision, vault_context)
    agent_outputs = list(state["agent_outputs"].values())

    # MCP — collect the provenance every agent attached to its output.
    mcp_sources: list[str] = []
    for out in agent_outputs:
        mcp_sources.extend(out.raw_data.get("mcp_sources", []))
    mcp_sources = list(dict.fromkeys(mcp_sources))  # dedupe, order-preserving
    mcp_used = any(not s.startswith("[MOCK] ") for s in mcp_sources)

    # Research provenance — the real URLs the Research agent cited (mock sources
    # carry the "[MOCK] " prefix and are stripped, so this is empty in mock mode).
    research_out = state["agent_outputs"].get("research")
    research_sources: list[str] = []
    if research_out:
        research_sources = [
            s for s in research_out.raw_data.get("mcp_sources", [])
            if not s.startswith("[MOCK] ")
        ]

    response = BoardResponse(
        company_id=company_id,
        agent_outputs=agent_outputs,
        debate_rounds=state.get("debate_rounds", []),
        consensus=state.get("consensus"),
        recommendation=state["recommendation"],
        mcp_used=mcp_used,
        mcp_sources=mcp_sources,
        research_sources=research_sources,
        mock_mode=not settings.is_live,
        used_paths=bundle.used_paths,
    )
    return response, bundle.used_paths


def run_board(company_id: str, profile: CompanyProfile, decision: Decision) -> BoardResponse:
    """Synchronous wrapper around the async graph — used by tests and any sync caller."""
    response, _used = asyncio.run(build_response(company_id, profile, decision))
    return response


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "FounderOS API is running",
        "version": "2.0.0",
        "llm_mode": "live" if settings.is_live else "mock",
        "model": settings.qwen_model if settings.is_live else "mock-fixture",
        "tip": None if settings.is_live else "Set QWEN_API_KEY and USE_MOCK_LLM=false in .env to go live.",
    }


@app.post("/api/analyze", response_model=BoardResponse)
@limiter.limit(ANALYZE_RATE_LIMIT)
async def analyze(request: Request, body: AnalyzeRequest):
    """
    Evaluate one company decision and return a board memo.
    Runs the full board (LangGraph) and writes the decision back to the vault.
    """
    # Profile: use the supplied one, else hydrate from the vault's _profile.md
    # (stubbed company picker → vault folder). Resolved BEFORE the try so the
    # 422 isn't swallowed into a 500 by the pipeline catch-all.
    profile = body.profile or vault.read_profile(body.company_id)
    if profile is None:
        raise HTTPException(
            status_code=422,
            detail=f"No stored profile for company '{body.company_id}' — "
                   "include a company profile with the first decision.",
        )

    try:
        response, _used = await build_response(body.company_id, profile, body.decision)

        # Persist the decision + company identity to the vault (durable) + the
        # request store (for GET).
        decision_id = vault.write_back(
            company_id=body.company_id,
            decision=body.decision,
            recommendation=response.recommendation,
            learnings=[d.position for d in response.recommendation.dissent],
            profile=profile,
        )
        responses_store[response.response_id] = {
            "response": response.model_dump(),
            "company_id": body.company_id,
            "decision_id": decision_id,
        }

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception("Board pipeline failed for company %s", body.company_id)
        raise HTTPException(status_code=500, detail="Board pipeline failed. Please try again.")


@app.get("/api/response/{response_id}")
def get_response(response_id: str):
    """Fetch a previously generated board response."""
    record = responses_store.get(response_id)
    if not record:
        raise HTTPException(status_code=404, detail="Response not found")
    return record["response"]


@app.post("/api/feedback")
@limiter.limit(FEEDBACK_RATE_LIMIT)
def submit_feedback(request: Request, body: FeedbackRequest):
    """
    The outcome loop — record what actually happened against the decision note.
    """
    record = responses_store.get(body.response_id)
    if not record:
        raise HTTPException(status_code=404, detail="Response not found")

    ok = vault.record_outcome(
        company_id=record["company_id"],
        decision_id=record["decision_id"],
        outcome=body.outcome or "",
        notes=body.notes or "",
    )
    record["response"]["_outcome"] = body.outcome

    return {
        "status": "ok",
        "written_to_vault": ok,
        "message": "Outcome recorded. The board will remember this next time.",
    }


@app.get("/api/company/{company_id}")
def get_company(company_id: str):
    """The company's decision history from the vault index."""
    try:
        return {
            "company_id": company_id,
            "history": vault.history(company_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to fetch history for company %s", company_id)
        raise HTTPException(status_code=500, detail="Could not retrieve company history.")


# ─────────────────────────────────────────────
# Run directly: python -m backend.main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Port 7860 is the Hugging Face Docker default (Decision #8).
    uvicorn.run("backend.main:app", host="0.0.0.0", port=7860, reload=True)
