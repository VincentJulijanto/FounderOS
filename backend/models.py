from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import uuid


# ─────────────────────────────────────────────
# Live-LLM coercion helpers
# ─────────────────────────────────────────────
# Real Qwen output sometimes returns a list (or dict) where the schema expects a
# single string. Mock fixtures are already well-typed, so these are no-ops in
# mock mode. Kept from the pre-pivot model — the live-mode messiness is unchanged.

def _to_str(v: Any) -> Any:
    """Coerce live-LLM values into a string for str-typed fields.

    Real Qwen is nondeterministic about types: a field declared as str may come
    back as a bullet list, a dict, a number, or null. Normalize them all; leave
    actual strings untouched.
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
    """Extract a float from messy live-LLM score values ('8/10', '7.5', 'high')."""
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


# ─────────────────────────────────────────────
# Input Models — company + one decision (the evaluator intake)
# ─────────────────────────────────────────────

class Financials(BaseModel):
    """Freeform financial context — the operator fills in what they have."""
    revenue_band: str = ""                    # e.g. "SGD 1–5M ARR"
    margin: Optional[str] = None              # e.g. "~30% gross"
    cash_position: Optional[str] = None       # e.g. "18 months runway"

    @field_validator("revenue_band", "margin", "cash_position", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v) if v is not None else v


class CompanyProfile(BaseModel):
    company_name: str
    sector: str                               # e.g. "regional logistics", "D2C skincare"
    stage: str                                # e.g. "early-revenue", "scaling", "mature"
    business_model: str                       # e.g. "B2B SaaS", "marketplace", "retail"
    size_band: str                            # e.g. "1–10", "11–50", "51–200" employees
    financials: Financials = Field(default_factory=Financials)

    model_config = {"json_schema_extra": {
        "example": {
            "company_name": "Kirana Logistics",
            "sector": "regional last-mile logistics",
            "stage": "scaling",
            "business_model": "B2B logistics SaaS + fleet ops",
            "size_band": "51–200",
            "financials": {
                "revenue_band": "SGD 8–12M ARR",
                "margin": "~22% gross",
                "cash_position": "14 months runway",
            },
        }
    }}


class Constraints(BaseModel):
    budget: Optional[str] = None
    timeline: Optional[str] = None


class Decision(BaseModel):
    question: str                             # the call being brought to the board
    context: Optional[str] = None             # background the operator wants on the table
    constraints: Constraints = Field(default_factory=Constraints)
    # Alternative approaches to THIS one decision (not separate decisions).
    # Scout frames them when the operator leaves this empty.
    options: Optional[List[str]] = None

    model_config = {"json_schema_extra": {
        "example": {
            "question": "Should we expand into the Vietnam market next quarter?",
            "context": "Two anchor customers have asked us to serve their Vietnam routes.",
            "constraints": {"budget": "SGD 500k", "timeline": "6 months"},
            "options": [
                "Full subsidiary in Ho Chi Minh City",
                "Asset-light partnership with a local 3PL",
                "Hold and deepen the current market",
            ],
        }
    }}


class AnalyzeRequest(BaseModel):
    company_id: str                           # from the company picker → vault folder
    profile: Optional[CompanyProfile] = None  # if None, hydrated from the vault
    decision: Decision


# ─────────────────────────────────────────────
# Vault interface models (persistence — signatures per the contract)
# ─────────────────────────────────────────────

class VaultNote(BaseModel):
    """One entry in a company's vault index — enough to rank without reading the body."""
    path: str                                 # filename within the company's vault folder
    frontmatter: Dict[str, Any] = {}          # {type, decision_id, date, recommendation, outcome}
    summary: str = ""                         # one line, for the LLM selector


class ContextBundle(BaseModel):
    """What vault.read returns: the bodies of the notes the selector chose, + provenance."""
    notes: List[str] = []                     # bodies of the selected notes only
    used_paths: List[str] = []                # which notes informed this run

    def as_prompt_block(self) -> str:
        """Render the selected notes into a compact block for agent prompts."""
        if not self.notes:
            return "No prior board history for this company — treat as a first session."
        return "\n\n---\n\n".join(self.notes)


# ─────────────────────────────────────────────
# Agent Output Models (carried over unchanged in shape)
# ─────────────────────────────────────────────

class AgentOutput(BaseModel):
    agent_name: str                           # canonical agent-name string
    role: str
    analysis: str
    score: Optional[float] = None             # 0–10
    key_findings: List[str] = []
    concerns: List[str] = []
    recommendations: List[str] = []
    raw_data: Dict[str, Any] = {}


# ─────────────────────────────────────────────
# Debate & Conflict Models (carried over unchanged — the debate is the main event)
# ─────────────────────────────────────────────

class ConflictPoint(BaseModel):
    topic: str
    agent_a: str
    agent_a_position: str
    agent_b: str
    agent_b_position: str
    severity: str   # "low" | "medium" | "high"
    resolved: bool = False


class DebateRound(BaseModel):
    round_number: int
    conflicts_identified: List[ConflictPoint]
    revised_positions: Dict[str, str]
    resolution_achieved: bool
    moderator_summary: str


class ConsensusReport(BaseModel):
    """
    Quantified outcome of the debate. consensus_score is a *resolution rate* — how
    much of the severity-weighted disagreement the board resolved — NOT a measure
    of decision quality. Unresolved conflicts are a feature: they become the memo's
    auditable dissent record. Labels describe agreement only.
    """
    consensus_score: float
    label: str
    total_conflicts: int
    resolved_conflicts: int
    unresolved_conflicts: List[ConflictPoint] = []
    rounds_used: int
    summary: str


# ─────────────────────────────────────────────
# Board Memo Models (the evaluator output)
# ─────────────────────────────────────────────

class OptionAssessment(BaseModel):
    """One per decision.options entry (1:1 with the alternatives on the table)."""
    option: str
    assessment: str
    verdict: Optional[str] = None             # e.g. "favoured", "viable", "avoid"

    @field_validator("option", "assessment", "verdict", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v) if v is not None else v


class Dissent(BaseModel):
    """The auditable dissent record — objections that did NOT get resolved."""
    agent: str                                # canonical agent-name string
    position: str

    @field_validator("agent", "position", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v)


class Phase(BaseModel):
    name: str                                 # e.g. "Validate", "Pilot", "Scale"
    objective: str
    actions: List[str] = []
    timeframe: Optional[str] = None

    @field_validator("name", "objective", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v)

    @field_validator("actions", mode="before")
    @classmethod
    def _coerce_actions(cls, v):
        return _items_to_str(v)


class ExecutionPlan(BaseModel):
    """Phased execution plan — replaces the old lean-canvas plan."""
    phases: List[Phase] = []


class BoardRecommendation(BaseModel):
    """The board memo core — what the Chair (venture_partner) writes."""
    recommendation: Literal["proceed", "hold", "conditional"]
    confidence: Literal["low", "medium", "high"]
    rationale: str                            # plain-language "why this call"
    missing_inputs: List[str] = []            # trust posture — what we'd need to be surer
    options_assessed: List[OptionAssessment] = []
    dissent: List[Dissent] = []               # the auditable dissent record
    what_would_change_this_call: str = ""     # the conditions that flip the recommendation
    execution_plan: ExecutionPlan = Field(default_factory=ExecutionPlan)
    financial_view: str = ""                  # plain-language financial read
    risks: List[str] = []
    disclaimer: str = (
        "Advisory output from an AI board, not a fiduciary board decision. "
        "The operator owns the call."
    )

    # Live Qwen coercion for the free-text and list fields.
    @field_validator("rationale", "what_would_change_this_call", "financial_view",
                     "disclaimer", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        return _to_str(v) if v is not None else v

    @field_validator("missing_inputs", "risks", mode="before")
    @classmethod
    def _coerce_lists(cls, v):
        return _items_to_str(v)

    @field_validator("recommendation", mode="before")
    @classmethod
    def _coerce_recommendation(cls, v):
        s = _to_str(v).strip().lower()
        if s in ("proceed", "go", "yes", "approve"):
            return "proceed"
        if s in ("hold", "no", "reject", "pause", "wait"):
            return "hold"
        return "conditional"

    @field_validator("confidence", mode="before")
    @classmethod
    def _coerce_confidence(cls, v):
        s = _to_str(v).strip().lower()
        if "high" in s:
            return "high"
        if "low" in s:
            return "low"
        return "medium"


# ─────────────────────────────────────────────
# API Response envelope
# ─────────────────────────────────────────────

class BoardResponse(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    agent_outputs: List[AgentOutput]
    debate_rounds: List[DebateRound]
    consensus: Optional[ConsensusReport] = None
    recommendation: BoardRecommendation       # the memo
    mcp_used: bool = False
    mcp_sources: List[str] = []
    mock_mode: bool = False                   # True when built from mock fixtures (no API key)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Feedback (the outcome loop → vault write-back)
# ─────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    response_id: str
    outcome: Optional[str] = None             # what actually happened
    notes: Optional[str] = None
