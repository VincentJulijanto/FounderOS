# FounderOS — Technical Architecture

## System Overview

```
User Input (Profile)
        │
        ▼
┌──────────────────────────────────────────────────┐
│                 FastAPI Backend                   │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Scout   │  │  Trend   │  │ Finance  │  ← parallel
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │             │
│       └──────────────┼──────────────┘             │
│                      │                           │
│              ┌───────┴───────┐                   │
│              │  Growth Agent │                   │
│              └───────┬───────┘                   │
│                      │                           │
│              ┌───────┴───────┐                   │
│              │ Skeptic Agent │ ← challenges all  │
│              └───────┬───────┘                   │
│                      │                           │
│           ┌──────────┴──────────┐                │
│           │   Debate Engine     │ ← conflict res │
│           └──────────┬──────────┘                │
│                      │                           │
│           ┌──────────┴──────────┐                │
│           │  Venture Partner    │ ← final call   │
│           └──────────┬──────────┘                │
│                      │                           │
│    ┌─────────────────┼─────────────────┐         │
│    │  Memory System  │                 │         │
│    │  ┌──────────┐   │  ┌──────────┐   │         │
│    │  │ Episodic │   │  │ Semantic │   │         │
│    │  └──────────┘   │  └──────────┘   │         │
│    └─────────────────┴─────────────────┘         │
└──────────────────────────────────────────────────┘
                       │
                       ▼
               VentureRecommendation
            (top ideas + execution plan)
```

---

## Agent Architecture

Each agent is a Python class extending `BaseAgent`:

```
BaseAgent
├── _call_claude(system, user_msg) → str    # Claude API call
├── _parse_json(text) → dict               # JSON extraction
├── _format_profile(profile) → str         # Shared formatter
└── analyze(profile, context) → AgentOutput  # Override in subclass
```

### Agent Data Flow

```
UserProfile + context_dict
        │
        ▼
 agent.analyze()
        │
        ├─ _format_profile(profile)
        ├─ Build user_message with context
        ├─ _call_claude(SYSTEM_PROMPT, user_message)
        ├─ _parse_json(raw_response)
        └─ return AgentOutput(...)
```

---

## Debate Engine Architecture

```
Step 1: Conflict Detection
  all_agent_outputs → detect_conflicts() → [ConflictPoint, ...]

Step 2: Debate Rounds (up to 3)
  For each round:
    conflicts + agent_outputs → Claude → DebateRound
    (agents argue, revise positions, moderator decides)
    if resolution_achieved: break

Step 3: Consensus Summary
  debate_rounds → _build_consensus_summary() → str

Step 4: Pass to Venture Partner
  consensus_summary → VenturePartner.analyze()
```

---

## Memory Architecture

### Episodic Memory (PostgreSQL)
```
Table: episodic_memory
├── user_id
├── session_id
├── recommendation_id
├── recommended_idea
├── startup_score
├── outcome (launched | abandoned | in_progress)
└── user_feedback
```

### Semantic Memory (PostgreSQL)
```
Table: semantic_memory
├── user_id
├── insight_type (preference | pattern | constraint)
├── key (e.g. "business_model_preference")
├── value (e.g. "B2B over B2C")
├── confidence (increments with repeated evidence)
└── evidence
```

### Memory Flow
```
New session starts
      │
      ▼
 Load episodic history  +  semantic insights
      │
      ▼
 Pass as context to Venture Partner
      │
      ▼
 Session completes → update episodic DB
      │
      ▼
 Extract semantic insights (Claude analysis)
      │
      ▼
 Upsert semantic DB (confidence++)
```

---

## API Architecture

```
POST /api/analyze
  Request:  { profile: UserProfile }
  Process:  run_agent_society(profile)
  Response: VentureRecommendation

GET  /api/recommendation/{id}
  Response: VentureRecommendation (from store)

POST /api/feedback
  Request:  { recommendation_id, outcome, notes }
  Process:  update_outcome() → trigger semantic extraction
  Response: { status: "ok" }

GET  /api/memory/{user_id}
  Response: { history: [...], semantic_insights: [...] }
```

---

## Data Models

```
UserProfile
├── user_id, name, background
├── skills[], budget, weekly_hours
├── interests[], goals

AgentOutput
├── agent_name, role
├── analysis (str)
├── score (0-10)
├── key_findings[], concerns[], recommendations[]

ConflictPoint
├── topic, severity
├── agent_a + agent_a_position
├── agent_b + agent_b_position

DebateRound
├── round_number
├── conflicts_identified[]
├── revised_positions{}
├── resolution_achieved, moderator_summary

StartupIdea
├── name, tagline, description, target_market
├── startup_score, feasibility_score, market_attractiveness_score
├── founder_fit_score, risk_score
├── revenue_potential, time_to_launch, initial_investment

ExecutionPlan
├── startup_name, value_proposition, customer_persona
├── lean_canvas (LeanCanvas)
├── mvp_scope, landing_page_copy
├── marketing_strategy, customer_acquisition_plan
├── elevator_pitch, customer_outreach_templates{}
├── thirty_day_roadmap[]

VentureRecommendation
├── user_profile, agent_outputs[]
├── debate_rounds[], top_ideas[]
├── recommended_idea, execution_plan
└── final_memo
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Claude (Anthropic) | Best reasoning, structured output |
| Framework | FastAPI | Async, auto-docs, Pydantic native |
| Orchestration | Direct + LangGraph | Simple first, LangGraph for scale |
| Memory | PostgreSQL | Reliable, queryable, production-ready |
| Frontend | Next.js 14 + Tailwind | App Router, TypeScript, fast dev |
| Deployment | Vercel (FE) + Railway (BE) | Free tier for hackathon |
