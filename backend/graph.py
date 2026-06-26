"""
FounderOS — LangGraph Orchestration (Phase 3)

Replaces the sequential agent loop with a StateGraph. The three analyst agents
(Trend, Finance, Growth) fan out in parallel via asyncio.gather; every other stage
runs sequentially because of real data dependencies.

Flow:
    scout → analysts (Trend ∥ Finance ∥ Growth) → skeptic → founder_fit → debate → venture_partner

Agents are synchronous (def analyze), so each parallel analyst is run in a worker
thread via asyncio.to_thread — this yields genuine concurrency in live mode where
the LLM call blocks on network I/O.
"""

import asyncio
import operator
import time
from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, END

from .models import UserProfile, AgentOutput
from .agents import (
    OpportunityScoutAgent,
    TrendAnalystAgent,
    FinanceAgent,
    GrowthAgent,
    SkepticAgent,
    FounderFitAgent,
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
    startup_profile: UserProfile
    memory_context: str
    opportunities: List[dict]

    # Reducers let nodes contribute partial updates that merge cleanly.
    agent_outputs: Annotated[Dict[str, AgentOutput], _merge_outputs]
    errors: Annotated[List[str], operator.add]

    # Filled by later nodes
    debate_rounds: list
    debate_summary: str
    consensus: Any
    top_ideas: list
    execution_plan: Any
    final_memo: str


# ─────────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────────

def scout_node(state: GraphState) -> dict:
    """Sequential — every downstream agent depends on the opportunities Scout finds."""
    profile = state["startup_profile"]
    out = OpportunityScoutAgent().analyze(profile)
    opportunities = out.raw_data.get("opportunities", [])
    return {
        "agent_outputs": {"Opportunity Scout": out},
        "opportunities": opportunities,
    }


async def analysts_node(state: GraphState) -> dict:
    """Parallel fan-out — Trend, Finance, Growth run concurrently and must all finish here."""
    profile = state["startup_profile"]
    context = {"opportunities": state.get("opportunities", [])}

    trend, finance, growth = TrendAnalystAgent(), FinanceAgent(), GrowthAgent()

    start = time.perf_counter()
    results = await asyncio.gather(
        asyncio.to_thread(trend.analyze, profile, context),
        asyncio.to_thread(finance.analyze, profile, context),
        asyncio.to_thread(growth.analyze, profile, context),
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - start

    outputs: Dict[str, AgentOutput] = {}
    errors: List[str] = []
    for label, res in zip(("Trend Analyst", "Finance Agent", "Growth Agent"), results):
        if isinstance(res, Exception):
            errors.append(f"{label} failed: {res}")
        else:
            outputs[label] = res

    print(f"[graph] analysts (Trend ∥ Finance ∥ Growth) completed in {elapsed:.3f}s")

    if errors:  # a missing analyst breaks the response shape — surface it
        raise RuntimeError("; ".join(errors))

    return {"agent_outputs": outputs}


def skeptic_node(state: GraphState) -> dict:
    """Sequential — needs the analysts' financial + market findings to reality-check."""
    profile = state["startup_profile"]
    outputs = state["agent_outputs"]

    finance_output = outputs.get("Finance Agent")
    trend_output = outputs.get("Trend Analyst")
    financial_analysis = finance_output.raw_data.get("financial_analysis", []) if finance_output else []
    market_analysis = trend_output.raw_data.get("market_analysis", []) if trend_output else []

    out = SkepticAgent().analyze(
        profile,
        {
            "opportunities": state.get("opportunities", []),
            "financial_analysis": financial_analysis,
            "market_analysis": market_analysis,
        },
    )
    return {"agent_outputs": {"Skeptic Agent": out}}


def founder_fit_node(state: GraphState) -> dict:
    """Sequential — checks the human side after the Skeptic's challenge."""
    profile = state["startup_profile"]
    out = FounderFitAgent().analyze(profile, {"opportunities": state.get("opportunities", [])})
    return {"agent_outputs": {"Founder-Fit Agent": out}}


def debate_node(state: GraphState) -> dict:
    """Sequential — reconciles conflicts across all six analyst/challenge agents."""
    profile = state["startup_profile"]
    outputs = state["agent_outputs"]

    profile_context = (
        f"Founder: {profile.name}, Budget: SGD {profile.budget}, "
        f"Hours/week: {profile.weekly_hours}, Goals: {profile.goals}\n"
        f"Memory context:\n{state.get('memory_context', '')}"
    )
    debate_rounds, consensus = DebateEngine().run(outputs, profile_context)
    # debate_summary mirrors consensus.summary so VP context + response shape are unchanged.
    return {
        "debate_rounds": debate_rounds,
        "debate_summary": consensus.summary,
        "consensus": consensus,
    }


def venture_partner_node(state: GraphState) -> dict:
    """Sequential — final synthesis into ranked ideas + execution plan."""
    profile = state["startup_profile"]
    outputs = state["agent_outputs"]

    vp = VenturePartnerAgent()
    vp_context = {
        "scout_output": outputs.get("Opportunity Scout"),
        "trend_output": outputs.get("Trend Analyst"),
        "finance_output": outputs.get("Finance Agent"),
        "growth_output": outputs.get("Growth Agent"),
        "skeptic_output": outputs.get("Skeptic Agent"),
        "founder_fit_output": outputs.get("Founder-Fit Agent"),
        "debate_summary": state.get("debate_summary", ""),
        "memory_context": state.get("memory_context", ""),
    }
    vp_out = vp.analyze(profile, vp_context)
    top_ideas, execution_plan = vp.build_structured_recommendation(vp_out.raw_data, profile)

    return {
        "agent_outputs": {"Venture Partner": vp_out},
        "top_ideas": top_ideas,
        "execution_plan": execution_plan,
        "final_memo": vp_out.analysis,
    }


# ─────────────────────────────────────────────
# Graph assembly
# ─────────────────────────────────────────────

def build_graph():
    """Compile the FounderOS agent-society StateGraph."""
    g = StateGraph(GraphState)

    g.add_node("scout", scout_node)
    g.add_node("analysts", analysts_node)
    g.add_node("skeptic", skeptic_node)
    g.add_node("founder_fit", founder_fit_node)
    g.add_node("debate", debate_node)
    g.add_node("venture_partner", venture_partner_node)

    g.set_entry_point("scout")
    g.add_edge("scout", "analysts")
    g.add_edge("analysts", "skeptic")
    g.add_edge("skeptic", "founder_fit")
    g.add_edge("founder_fit", "debate")
    g.add_edge("debate", "venture_partner")
    g.add_edge("venture_partner", END)

    return g.compile()


# Compile once at import — the graph is stateless across runs.
_GRAPH = build_graph()


async def run_graph(profile: UserProfile, memory_context: str = "") -> GraphState:
    """
    Run the full agent society and return the final graph state.

    The state contains: agent_outputs (all 7), debate_rounds, debate_summary,
    consensus (ConsensusReport), top_ideas, execution_plan, final_memo, errors.
    """
    initial: GraphState = {
        "startup_profile": profile,
        "memory_context": memory_context,
        "opportunities": [],
        "agent_outputs": {},
        "errors": [],
    }
    return await _GRAPH.ainvoke(initial)
