from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


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
