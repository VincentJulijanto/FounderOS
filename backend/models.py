from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
# Live-LLM coercion helpers
# ─────────────────────────────────────────────
# Real Qwen output sometimes returns a list (or dict) where the schema expects a
# single string — e.g. LeanCanvas fields came back as bullet lists in live mode
# (Sprint B). Mock fixtures are already strings, so these are no-ops in mock mode.

def _to_str(v: Any) -> Any:
    """Coerce live-LLM values into a string for str-typed fields.

    Real Qwen is nondeterministic about types: a field declared as str may come
    back as a bullet list, a dict, a number (e.g. initial_investment=4850), or
    null. Normalize them all; leave actual strings untouched.
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "\n".join(str(x) for x in v)
    if isinstance(v, dict):
        return "\n".join(f"{k}: {val}" for k, val in v.items())
    return str(v)  # int / float / bool


def _to_float(v: Any) -> Any:
    """Extract a float from messy live-LLM score values ('8/10', '7.5', 'high').

    Returns the first number found; falls back to None so the field default (or
    Pydantic's own error) applies if nothing numeric is present.
    """
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        import re
        m = re.search(r"-?\d+(?:\.\d+)?", v)
        return float(m.group()) if m else None
    return v


def _items_to_str(v: Any) -> Any:
    """Coerce each element of a list to a string (for List[str] fields)."""
    if isinstance(v, list):
        return [_to_str(x) if isinstance(x, (list, dict)) else str(x) for x in v]
    return v


def _values_to_str(v: Any) -> Any:
    """Coerce each value of a dict to a string (for Dict[str, str] fields)."""
    if isinstance(v, dict):
        return {str(k): _to_str(val) for k, val in v.items()}
    return v


# ─────────────────────────────────────────────
# Input Models
# ─────────────────────────────────────────────

class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    background: str              # e.g. "NUS Computer Science student, Year 2"
    skills: List[str]            # e.g. ["Python", "UI/UX", "Social Media"]
    budget: float                # in SGD
    weekly_hours: int
    interests: List[str]         # e.g. ["EdTech", "Sustainability", "Gaming"]
    goals: str                   # e.g. "Earn $1k/month side income"

    model_config = {"json_schema_extra": {
        "example": {
            "name": "Alex Tan",
            "background": "NUS Computer Science student with $500 budget and 10 hours per week",
            "skills": ["Python", "React", "Data Analysis"],
            "budget": 500,
            "weekly_hours": 10,
            "interests": ["EdTech", "Productivity", "AI"],
            "goals": "Earn $1,000/month passive side income within 3 months"
        }
    }}


# ─────────────────────────────────────────────
# Agent Output Models
# ─────────────────────────────────────────────

class AgentOutput(BaseModel):
    agent_name: str
    role: str
    analysis: str
    score: Optional[float] = None       # 0–10
    key_findings: List[str] = []
    concerns: List[str] = []
    recommendations: List[str] = []
    raw_data: Dict[str, Any] = {}


# ─────────────────────────────────────────────
# Debate & Conflict Models
# ─────────────────────────────────────────────

class ConflictPoint(BaseModel):
    topic: str
    agent_a: str
    agent_a_position: str
    agent_b: str
    agent_b_position: str
    severity: str   # "low" | "medium" | "high"
    resolved: bool = False   # set per round; backward-compatible default


class DebateRound(BaseModel):
    round_number: int
    conflicts_identified: List[ConflictPoint]
    revised_positions: Dict[str, str]   # agent_name -> revised stance
    resolution_achieved: bool
    moderator_summary: str


class ConsensusReport(BaseModel):
    """
    Quantified outcome of the debate. consensus_score is a *resolution rate* —
    how much of the severity-weighted disagreement the society resolved — NOT a
    measure of idea quality. A run that resolves one trivial conflict (10.0) is
    not "better" than one that surfaces three hard ones and resolves two (6.0).
    Labels describe agreement only.
    """
    consensus_score: float                       # 0–10, severity-weighted resolution rate
    label: str                                   # agreement label (see debate_engine bands)
    total_conflicts: int
    resolved_conflicts: int
    unresolved_conflicts: List[ConflictPoint] = []   # structured, not just prose
    rounds_used: int
    summary: str                                 # human-readable write-up


# ─────────────────────────────────────────────
# Startup Idea Models
# ─────────────────────────────────────────────

class StartupIdea(BaseModel):
    name: str
    tagline: str
    description: str
    target_market: str

    # Scores (0–10)
    startup_score: float
    feasibility_score: float
    market_attractiveness_score: float
    founder_fit_score: float
    risk_score: float   # lower = less risky

    # Estimates
    revenue_potential: str
    estimated_monthly_revenue: str
    time_to_launch: str
    initial_investment: str
    risk_level: str     # "Low" | "Medium" | "High"

    # Live Qwen sometimes returns lists/dicts for text fields — coerce to str.
    @field_validator(
        "name", "tagline", "description", "target_market", "revenue_potential",
        "estimated_monthly_revenue", "time_to_launch", "initial_investment", "risk_level",
        mode="before",
    )
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v)

    @field_validator(
        "startup_score", "feasibility_score", "market_attractiveness_score",
        "founder_fit_score", "risk_score", mode="before",
    )
    @classmethod
    def _coerce_score(cls, v):
        coerced = _to_float(v)
        return coerced if coerced is not None else 0.0


# ─────────────────────────────────────────────
# Execution Plan Models
# ─────────────────────────────────────────────

class LeanCanvas(BaseModel):
    problem: str
    solution: str
    unique_value_proposition: str
    unfair_advantage: str
    customer_segments: str
    key_metrics: str
    channels: str
    cost_structure: str
    revenue_streams: str

    # All fields are text; live Qwen often returns bullet lists here (Sprint B).
    @field_validator("*", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v)


class ExecutionPlan(BaseModel):
    startup_name: str
    value_proposition: str
    customer_persona: str
    lean_canvas: LeanCanvas
    mvp_scope: str
    landing_page_copy: str
    marketing_strategy: str
    customer_acquisition_plan: str
    elevator_pitch: str
    customer_outreach_templates: Dict[str, str]   # e.g. {"cold_email": "...", "dm": "..."}
    thirty_day_roadmap: List[str]                 # list of daily/weekly milestones

    # Coerce live Qwen lists/dicts into the declared shapes.
    @field_validator(
        "startup_name", "value_proposition", "customer_persona", "mvp_scope",
        "landing_page_copy", "marketing_strategy", "customer_acquisition_plan",
        "elevator_pitch", mode="before",
    )
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v)

    @field_validator("customer_outreach_templates", mode="before")
    @classmethod
    def _coerce_templates(cls, v):
        return _values_to_str(v)

    @field_validator("thirty_day_roadmap", mode="before")
    @classmethod
    def _coerce_roadmap(cls, v):
        return _items_to_str(v)


# ─────────────────────────────────────────────
# Final Recommendation
# ─────────────────────────────────────────────

class VentureRecommendation(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_profile: UserProfile
    agent_outputs: List[AgentOutput]
    debate_rounds: List[DebateRound]
    debate_summary: str = ""                       # consensus write-up (mirrors consensus.summary)
    consensus: Optional[ConsensusReport] = None    # quantified debate outcome
    top_ideas: List[StartupIdea]                  # top 3
    recommended_idea: Optional[StartupIdea] = None  # None only if model returned no ideas
    execution_plan: Optional[ExecutionPlan] = None
    final_memo: str                         # investment-style write-up

    # MCP (Phase 6) — provenance of the live market signals used this run.
    mcp_used: bool = False                   # True if any MCP call returned live data
    mcp_sources: List[str] = []              # deduped union of all agents' mcp_sources

    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# API Request/Response Models
# ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    profile: UserProfile


class FeedbackRequest(BaseModel):
    recommendation_id: str
    user_id: str
    pursued_idea: Optional[str] = None
    outcome: Optional[str] = None          # "launched" | "abandoned" | "in_progress"
    notes: Optional[str] = None
