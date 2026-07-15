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
    company_name: str = Field(max_length=100)
    sector: str = Field(max_length=200)
    stage: str = Field(max_length=100)
    business_model: str = Field(max_length=200)
    size_band: str = Field(max_length=50)
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
    question: str = Field(max_length=500)
    context: Optional[str] = Field(default=None, max_length=2000)
    constraints: Constraints = Field(default_factory=Constraints)
    options: Optional[List[str]] = None  # Scout frames these when left empty

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


_COMPANY_ID_PATTERN = r'^[a-z0-9][a-z0-9\-_]{0,49}$'


class AnalyzeRequest(BaseModel):
    company_id: str = Field(pattern=_COMPANY_ID_PATTERN)
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
    research_sources: List[str] = []          # real (non-mock) URLs the Research agent cited
    mock_mode: bool = False                   # True when built from mock fixtures (no API key)
    used_paths: List[str] = []                # vault notes that informed this run (provenance)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Feedback (the outcome loop → vault write-back)
# ─────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    response_id: str
    outcome: Optional[str] = None             # what actually happened
    notes: Optional[str] = None


# ─────────────────────────────────────────────
# Feedback Intelligence Council — Track 3: Agent Society
# ─────────────────────────────────────────────

class FeedbackNote(BaseModel):
    """One user-submitted feedback note read from the vault (type: feedback)."""
    text: str
    date: str = ""
    response_id: str = ""


class FeedbackTheme(BaseModel):
    """A recurring theme clustered from user feedback, post-council deliberation."""
    theme: str
    frequency: int = 1
    representative_quotes: List[str] = []
    priority: Literal["high", "medium", "low"] = "medium"
    thesis_aligned: bool = True


class CouncilTurn(BaseModel):
    """One agent's contribution to the council dialogue — makes the debate auditable."""
    agent: str                                # "feedback_analyst" | "feedback_skeptic" | "feedback_chair"
    message: str                              # what this agent said to the council
    challenges: List[str] = []               # skeptic only: specific objections raised


class BaselineComparison(BaseModel):
    """Single-agent baseline vs. council output — the measurable efficiency delta."""
    single_agent_summary: str                 # flat summary a lone agent would produce (no critical filter)
    council_corrections: List[str]            # specific things the council caught that baseline missed
    corrections_count: int                    # integer efficiency delta


class CouncilBriefRequest(BaseModel):
    company_id: str = Field(pattern=_COMPANY_ID_PATTERN)


class CouncilBriefResponse(BaseModel):
    """The Feedback Intelligence Council's output — agent dialogue + ranked brief + baseline delta."""
    company_id: str
    feedback_notes_read: int
    council_dialogue: List[CouncilTurn]       # full agent-to-agent exchange
    themes: List[FeedbackTheme]               # final ranked themes post-debate
    baseline_comparison: BaselineComparison
    ranked_brief: str                         # human-readable final output
    mock_mode: bool = False


# ─────────────────────────────────────────────
# Feature Delivery Loop — SWE ⇄ QA iteration (Track 3: Agent Society)
# ─────────────────────────────────────────────

class BuildSpec(BaseModel):
    """The Senior SWE's build spec for one feature — the artifact QA reviews."""
    feature_name: str
    problem: str = ""                         # the user need the feature answers
    scope: List[str] = []
    out_of_scope: List[str] = []
    data_touched: List[str] = []              # what user/company data the feature reads or stores
    implementation_steps: List[str] = []
    security_considerations: List[str] = []
    test_notes: List[str] = []

    _s = field_validator("problem", mode="before")(_to_str)
    _ls = field_validator(
        "scope", "out_of_scope", "data_touched", "implementation_steps",
        "security_considerations", "test_notes", mode="before",
    )(_items_to_str)


class QAIssue(BaseModel):
    """One problem QA found in a build spec."""
    severity: Literal["high", "medium", "low"] = "medium"
    category: Literal["bug", "leak", "breach", "gap"] = "bug"
    description: str
    location: str = ""                        # which part of the spec the issue lives in


class QARound(BaseModel):
    """One QA review pass over the spec — the loop's auditable unit."""
    round: int
    verdict: Literal["pass", "fail"]
    issues: List[QAIssue] = []


class SignalGate(BaseModel):
    """The Data Analyst's go/no-go: does the feedback represent enough users to build for?"""
    sufficient: bool
    rationale: str = ""


class FeatureLoopRequest(BaseModel):
    company_id: str = Field(pattern=_COMPANY_ID_PATTERN)
    theme: FeedbackTheme                      # the council theme to build (picked in the UI)
    feedback_notes_read: int = 0              # denominator for the signal gate


class FeatureLoopResponse(BaseModel):
    """One delivery-loop run: gate → build spec → QA rounds (⇄ SWE fixes) → release/hold."""
    company_id: str
    theme: FeedbackTheme
    gate: SignalGate
    loop_dialogue: List[CouncilTurn] = []     # analyst gate + every SWE/QA turn, in order
    build_spec: Optional[BuildSpec] = None    # final revision (None when gated out)
    qa_rounds: List[QARound] = []
    iterations: int = 0                       # number of QA reviews run
    status: Literal["released", "held", "insufficient_signal"]
    release_note_path: str = ""               # vault note written on release
    mock_mode: bool = False
