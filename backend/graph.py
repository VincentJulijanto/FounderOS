"""
FounderOS — LangGraph Orchestration (evaluator board)

The board evaluates ONE company decision. The four analyst agents (Trend, Finance,
Growth, Capability) fan out in parallel; every other stage runs sequentially because
of real data dependencies.

Flow:
    scout → analysts (trend ∥ finance ∥ growth ∥ capability) → skeptic → debate → venture_partner (Chair)

Node keys, agent_outputs keys, and the agents' `name` attributes all use the
canonical strings: scout · trend · finance · growth · skeptic · capability · venture_partner.

Agents are synchronous (def analyze), so each parallel analyst is run in a worker
thread via asyncio.to_thread — genuine concurrency in live mode where the LLM call
blocks on network I/O.
"""

import asyncio
import operator
import time
from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END

from .models import CompanyProfile, Decision, AgentOutput, BoardRecommendation
from .agents import (
    OpportunityScoutAgent,
    TrendAnalystAgent,
    FinanceAgent,
    GrowthAgent,
    SkepticAgent,
    CapabilityAgent,
    VenturePartnerAgent,
)
from .consensus.debate_engine import DebateEngine


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

def _merge_outputs(left: Dict[str, AgentOutput], right: Dict[str, AgentOutput]) -> Dict[str, AgentOutput]:
    """Reducer so each node merges its agent output(s) instead of overwriting the dict."""
    return {**left, **right}


class GraphState(TypedDict, total=False):
    company_profile: CompanyProfile
    decision: Decision
    vault_context: str            # prompt block from the vault (selective retrieval)
    options: List[str]            # framed by Scout

    # Reducers let nodes contribute partial updates that merge cleanly.
    agent_outputs: Annotated[Dict[str, AgentOutput], _merge_outputs]
    errors: Annotated[List[str], operator.add]

    # Filled by later nodes
    debate_rounds: list
    debate_summary: str
    consensus: Any
    recommendation: BoardRecommendation


def _base_context(state: GraphState) -> dict:
    """The context every agent needs: the decision + vault history."""
    return {
        "decision": state["decision"],
        "vault_context": state.get("vault_context", ""),
    }


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────

def scout_node(state: GraphState) -> dict:
    """Sequential — the board evaluates the options Scout frames."""
    profile = state["company_profile"]
    out = OpportunityScoutAgent().analyze(profile, _base_context(state))
    options = out.raw_data.get("options", [])
    # Push the framed options back onto the decision so downstream agents see them.
    decision = state["decision"].model_copy(update={"options": options})
    return {
        "agent_outputs": {"scout": out},
        "options": options,
        "decision": decision,
    }


async def analysts_node(state: GraphState) -> dict:
    """Parallel fan-out — Trend, Finance, Growth, Capability run concurrently."""
    profile = state["company_profile"]
    ctx = _base_context(state)

    trend, finance, growth, capability = (
        TrendAnalystAgent(), FinanceAgent(), GrowthAgent(), CapabilityAgent()
    )

    start = time.perf_counter()
    results = await asyncio.gather(
        asyncio.to_thread(trend.analyze, profile, ctx),
        asyncio.to_thread(finance.analyze, profile, ctx),
        asyncio.to_thread(growth.analyze, profile, ctx),
        asyncio.to_thread(capability.analyze, profile, ctx),
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - start

    outputs: Dict[str, AgentOutput] = {}
    errors: List[str] = []
    for key, res in zip(("trend", "finance", "growth", "capability"), results):
        if isinstance(res, Exception):
            errors.append(f"{key} failed: {res}")
        else:
            outputs[key] = res

    print(f"[graph] analysts (trend ∥ finance ∥ growth ∥ capability) completed in {elapsed:.3f}s")

    if errors:  # a missing analyst breaks the response shape — surface it
        raise RuntimeError("; ".join(errors))

    return {"agent_outputs": outputs}


def skeptic_node(state: GraphState) -> dict:
    """Sequential — the main event. Attacks the decision after the analysts weigh in."""
    profile = state["company_profile"]
    outputs = state["agent_outputs"]

    analyst_summary = "\n".join(
        f"- {outputs[k].role}: {outputs[k].analysis[:180]}"
        for k in ("trend", "finance", "growth", "capability")
        if k in outputs
    )
    ctx = {**_base_context(state), "analyst_summary": analyst_summary}
    out = SkepticAgent().analyze(profile, ctx)
    return {"agent_outputs": {"skeptic": out}}


def debate_node(state: GraphState) -> dict:
    """Sequential — reconciles conflicts across the whole board."""
    profile = state["company_profile"]
    decision = state["decision"]
    outputs = state["agent_outputs"]

    profile_context = (
        f"Company: {profile.company_name} ({profile.sector}, {profile.stage}). "
        f"Decision: {decision.question}\n"
        f"Prior board history:\n{state.get('vault_context', '')}"
    )
    debate_rounds, consensus = DebateEngine().run(outputs, profile_context)
    return {
        "debate_rounds": debate_rounds,
        "debate_summary": consensus.summary,
        "consensus": consensus,
    }


def venture_partner_node(state: GraphState) -> dict:
    """Sequential — the Chair synthesizes the debate into the board memo."""
    profile = state["company_profile"]
    decision = state["decision"]
    outputs = state["agent_outputs"]
    consensus = state.get("consensus")

    chair = VenturePartnerAgent()
    ctx = {
        **_base_context(state),
        "agent_outputs": outputs,
        "debate_summary": state.get("debate_summary", ""),
    }
    chair_out = chair.analyze(profile, ctx)
    recommendation = chair.build_recommendation(chair_out.raw_data, decision, consensus)

    return {
        "agent_outputs": {"venture_partner": chair_out},
        "recommendation": recommendation,
    }


# ─────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────

def build_graph():
    """Compile the FounderOS board StateGraph."""
    g = StateGraph(GraphState)

    g.add_node("scout", scout_node)
    g.add_node("analysts", analysts_node)
    g.add_node("skeptic", skeptic_node)
    g.add_node("debate", debate_node)
    g.add_node("venture_partner", venture_partner_node)

    g.set_entry_point("scout")
    g.add_edge("scout", "analysts")
    g.add_edge("analysts", "skeptic")
    g.add_edge("skeptic", "debate")
    g.add_edge("debate", "venture_partner")
    g.add_edge("venture_partner", END)

    return g.compile()


# Compile once at import — the graph is stateless across runs.
_GRAPH = build_graph()


async def run_graph(
    company_profile: CompanyProfile,
    decision: Decision,
    vault_context: str = "",
) -> GraphState:
    """
    Run the full board and return the final graph state.

    The state contains: agent_outputs (all 7), debate_rounds, debate_summary,
    consensus (ConsensusReport), recommendation (BoardRecommendation), errors.
    """
    initial: GraphState = {
        "company_profile": company_profile,
        "decision": decision,
        "vault_context": vault_context,
        "options": [],
        "agent_outputs": {},
        "errors": [],
    }
    return await _GRAPH.ainvoke(initial)
