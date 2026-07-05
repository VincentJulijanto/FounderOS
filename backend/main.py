"""
FounderOS — FastAPI Backend Entry Point (evaluator board)

Endpoints (contract in docs/architecture.md § API Architecture):
  POST /api/analyze              — Evaluate one company decision → BoardResponse
  GET  /api/response/{id}        — Fetch a saved BoardResponse
  POST /api/feedback             — Outcome loop → vault write-back
  GET  /api/company/{company_id} — The company's decision history (from the vault)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

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

app = FastAPI(
    title="FounderOS API",
    description="AI board of directors — evaluate one company decision, get a board memo",
    version="2.0.0",
)

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

    response = BoardResponse(
        company_id=company_id,
        agent_outputs=agent_outputs,
        debate_rounds=state.get("debate_rounds", []),
        consensus=state.get("consensus"),
        recommendation=state["recommendation"],
        mcp_used=mcp_used,
        mcp_sources=mcp_sources,
        mock_mode=not settings.is_live,
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
async def analyze(request: AnalyzeRequest):
    """
    Evaluate one company decision and return a board memo.
    Runs the full board (LangGraph) and writes the decision back to the vault.
    """
    # Profile: use the supplied one, else hydrate from the vault's _profile.md
    # (stubbed company picker → vault folder). Resolved BEFORE the try so the
    # 422 isn't swallowed into a 500 by the pipeline catch-all.
    profile = request.profile or vault.read_profile(request.company_id)
    if profile is None:
        raise HTTPException(
            status_code=422,
            detail=f"No stored profile for company '{request.company_id}' — "
                   "include a company profile with the first decision.",
        )

    try:
        response, _used = await build_response(request.company_id, profile, request.decision)

        # Persist the decision + company identity to the vault (durable) + the
        # request store (for GET).
        decision_id = vault.write_back(
            company_id=request.company_id,
            decision=request.decision,
            recommendation=response.recommendation,
            learnings=[d.position for d in response.recommendation.dissent],
            profile=profile,
        )
        responses_store[response.response_id] = {
            "response": response.model_dump(),
            "company_id": request.company_id,
            "decision_id": decision_id,
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Board pipeline failed: {str(e)}")


@app.get("/api/response/{response_id}")
def get_response(response_id: str):
    """Fetch a previously generated board response."""
    record = responses_store.get(response_id)
    if not record:
        raise HTTPException(status_code=404, detail="Response not found")
    return record["response"]


@app.post("/api/feedback")
def submit_feedback(request: FeedbackRequest):
    """
    The outcome loop — record what actually happened against the decision note.
    """
    record = responses_store.get(request.response_id)
    if not record:
        raise HTTPException(status_code=404, detail="Response not found")

    ok = vault.record_outcome(
        company_id=record["company_id"],
        decision_id=record["decision_id"],
        outcome=request.outcome or "",
        notes=request.notes or "",
    )
    # Mirror onto the in-memory snapshot too.
    record["response"]["_outcome"] = request.outcome

    return {
        "status": "ok",
        "written_to_vault": ok,
        "message": "Outcome recorded. The board will remember this next time.",
    }


@app.get("/api/company/{company_id}")
def get_company(company_id: str):
    """The company's decision history from the vault index."""
    return {
        "company_id": company_id,
        "history": vault.history(company_id),
    }


# ─────────────────────────────────────────────
# Run directly: python -m backend.main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Port 7860 is the Hugging Face Docker default (Decision #8).
    uvicorn.run("backend.main:app", host="0.0.0.0", port=7860, reload=True)
