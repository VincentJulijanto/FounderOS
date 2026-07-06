# FounderOS — Technical Architecture

> **Pivot in progress (Phase 0/1).** FounderOS is moving from an *idea generator* for aspiring
> founders to an *AI board/council* that helps operators of **existing businesses** evaluate a
> specific decision — "is this sound, and what are we missing?" — and get a board-ready memo back.
> This document is the **canonical, frozen Phase 0 contract** for that pivot. Both build lanes
> (backend + frontend) code against the contract in [§ Frozen I/O Contract](#frozen-io-contract).
> If a field needs to change, change it *here first*, then in code.

---

## The pivot in one paragraph

The old product took a **founder profile** (a static snapshot of a person) and *generated* a
startup idea plus a launch plan. The pipeline was a **generator**: it invented options from
nothing and its job was divergence. The new product takes a **company + one decision** and
*evaluates* it: is this call sound, what's missing, what would change it? The pipeline is now an
**evaluator**: its job is convergence — pressure-test one proposal against what we know about the
company and surface the gaps. The 7-agent debate machinery carries over unchanged in shape; what
changes is the **inputs** (company + decision, not a person), the **agent framing** (company-centric,
not founder-centric), the **memory** (a per-company Obsidian markdown vault with selective
retrieval + write-back, not an in-process per-user store), and the **output** (a board memo, not a
ranked idea list + lean canvas).

Consequence for the agents: the **Skeptic and the Debate Engine are now the main event**, not a
quality gate bolted onto idea generation. Judging a real decision *is* the product.

---

## The eight decisions (settled — build to these)

1. **Persistence: VAULT ONLY.** A per-company Obsidian markdown vault is the single source of
   durable memory. `backend/memory/episodic.py` + `semantic.py` (Postgres) stay **unwired and out
   of the path**. There is **no SQLite** (that earlier note was drift).
2. **Retrieval: LLM-driven note selection** over a small vault index (frontmatter + filenames +
   one-line summaries). **No embeddings, no RAG, no vector DB.**
3. **Auth / "company account": STUBBED.** A company picker that maps to a vault folder. No real
   auth this phase.
4. **Input unit: EVALUATOR — one decision per run.** Not idea-generation, not periodic review.
5. **Outcome/validation loop: folded into vault write-back** (decision → recommendation → later
   outcome). The memo carries the trust posture (a one-line disclaimer + explicit `missing_inputs`).
6. **Name: keep "FounderOS"** for now.
7. **Register: board-memo STRUCTURE, plain operator language.** No consultant/McKinsey jargon.
8. **Deployment: Hugging Face Spaces (Docker) for the backend, Vercel Hobby for the frontend.**
   A long-running container holds the ~90–240s debate run (serverless can't); both tiers are free
   and need no card. Vault path is configuration, not hardcoded; the free-tier filesystem is
   ephemeral (fine for a demo) with a seed vault baked into the image. See [§ Deployment](#deployment-decision-8)
   and `docs/deployment.md`.

---

## System Overview

```
Company picker (stubbed) ──► company_id
        │
        ▼
   Decision (the call being brought to the board)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│              FastAPI Backend (LangGraph)                  │
│                                                          │
│   vault.read(company_id, query) ──► ContextBundle         │
│        │  (LLM-selected relevant notes only)              │
│        ▼                                                  │
│              ┌───────────────┐                            │
│              │  Scout        │ ← frames/【generates】       │
│              └───────┬───────┘   the options on the table │
│                      │                                    │
│  ┌──────────┐  ┌─────┴────┐  ┌──────────┐  ┌───────────┐ │
│  │  Trend   │  │ Finance  │  │  Growth  │  │Capability │ ← parallel fan-out
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │
│       └──────────────┼─────────────┴──────────────┘       │
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │   Skeptic     │ ← THE MAIN EVENT: attacks  │
│              └───────┬───────┘   the decision's weak points│
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │ Debate Engine │ ← conflict → rounds →       │
│              └───────┬───────┘   consensus + dissent record│
│                      ▼                                    │
│              ┌───────────────┐                            │
│              │     Chair     │ ← writes the board memo    │
│              └───────┬───────┘                            │
│                      ▼                                    │
│   vault.write_back(company_id, decision, recommendation)  │
└──────────────────────────────────────────────────────────┘
                       │
                       ▼
                BoardResponse
        (memo: recommendation + dissent + missing inputs + phased plan)
```

There are **7 agents**: **Scout, Trend, Finance, Growth, Skeptic, Capability, Chair.**
(`capability` is the rebuilt `founder_fit` — see [§ Agents](#the-seven-agents-company-centric).)

---

## Frozen I/O Contract

> **This is the Phase 0 contract. It is frozen once the owner signs off.** Field shapes are shown
> as Pydantic-v2-style schemas for clarity; this document — not any `.py` file — is the source of
> truth until sign-off, after which Lane A implements `backend/models.py` to match and Lane B
> mirrors it in `frontend/src/app/studio/page.tsx`.

### Input

```
CompanyProfile:
    company_name:    str
    sector:          str                     # e.g. "regional logistics", "D2C skincare"
    stage:           str                     # e.g. "early-revenue", "scaling", "mature"
    business_model:  str                     # e.g. "B2B SaaS", "marketplace", "retail"
    size_band:       str                     # e.g. "1–10", "11–50", "51–200" employees
    financials:      Financials              # freeform — see below

Financials:                                  # all freeform; operator fills what they have
    revenue_band:    str                     # e.g. "SGD 1–5M ARR"
    margin:          Optional[str] = None    # e.g. "~30% gross"
    cash_position:   Optional[str] = None    # e.g. "18 months runway"

Decision:
    question:        str                     # the call being brought to the board
    context:         Optional[str] = None    # background the operator wants on the table
    constraints:     Constraints             # see below
    options:         Optional[list[str]] = None   # alternative approaches to THIS one decision; Scout frames them if empty

Constraints:
    budget:          Optional[str] = None
    timeline:        Optional[str] = None

AnalyzeRequest:
    company_id:      str                     # from the company picker → vault folder
    profile:         Optional[CompanyProfile] = None   # if None, hydrated from the vault
    decision:        Decision
```

**Dropped from the old founder intake** (per the recon keep/cut table): `name`, `weekly_hours`,
`skills`. `background`/`goals`/`budget`/`interests` are subsumed by `CompanyProfile` + `Decision`.

> **Options are alternative approaches to the *one* decision — not multiple separate decisions**
> (evaluator / one-decision-per-run). `decision.options` holds those alternatives (the Scout
> generates them when the operator leaves it empty), and the output's `options_assessed[]` maps
> **one-to-one** onto them.

### Output

```
BoardRecommendation:                         # the memo core
    recommendation:            Literal["proceed", "hold", "conditional"]
    confidence:                Literal["low", "medium", "high"]
    rationale:                 str           # plain-language "why this call"
    missing_inputs:            list[str]     # what we'd need to be more sure (trust posture)
    options_assessed:          list[OptionAssessment]   # one per decision.options entry (1:1)
    dissent:                   list[Dissent] # the auditable dissent record
    what_would_change_this_call: str         # the conditions that flip the recommendation
    execution_plan:            ExecutionPlan # phased — see below
    financial_view:            str           # plain-language financial read (operator language)
    risks:                     list[str]
    disclaimer:                str           # one line — advisory, not a fiduciary board

OptionAssessment:
    option:                    str
    assessment:                str
    verdict:                   Optional[str] = None   # e.g. "favoured", "viable", "avoid"

Dissent:
    agent:                     str           # canonical agent-name string
    position:                  str           # the objection that did NOT get resolved

ExecutionPlan:                               # phased (replaces the old lean-canvas plan)
    phases:                    list[Phase]

Phase:
    name:                      str           # e.g. "Validate", "Pilot", "Scale"
    objective:                 str
    actions:                   list[str]
    timeframe:                 Optional[str] = None
```

> **`financial_view` is deliberately a plain-language `str`, not a structured figures object.**
> Structured figures would imply real numbers we don't have (the trust gap), and prose matches
> decision #7 (plain operator language).

### Response envelope (refinement — see deviation note)

The API returns the memo **plus** the agent-society envelope the debate UI already renders
(`AgentDebate`, `CouncilReasoning`). `dissent[]` is *derived from* the unresolved conflicts +
revised positions in `debate_rounds`/`consensus` — it is the memo-facing distillation of them.

```
BoardResponse:
    response_id:     str
    company_id:      str
    agent_outputs:   list[AgentOutput]       # unchanged shape; carried over
    debate_rounds:   list[DebateRound]       # unchanged shape; carried over
    consensus:       Optional[ConsensusReport]
    recommendation:  BoardRecommendation     # the memo
    mcp_used:        bool                     # carried over from Phase 6
    mcp_sources:     list[str]
    mock_mode:       bool                     # True when built from mock fixtures — drives the
                                              # frontend "Sample data" disclosure badge
    used_paths:      list[str]                # vault notes that informed this run (provenance;
                                              # _-prefixed = identity context, not memory)
    created_at:      datetime
```

**Amendment (recorded):** `mock_mode` was added to the envelope so fixture output is always
disclosed in the UI; it is `not settings.is_live` at build time.

`AgentOutput`, `DebateRound`, `ConsensusReport`, `ConflictPoint` keep their existing shapes from
the current `models.py` — only their *content* becomes company/decision-centric.

### Vault interface (implemented — amendments recorded inline)

```
read(company_id: str, query: str) -> ContextBundle
    # Selects the relevant notes from the vault index (frontmatter + filename +
    # one-line summary) and returns only those. Never loads the whole vault.
    # Amendment: LLM-driven selection runs LIVE-ONLY, and only when the index
    # exceeds MAX_SELECTED_NOTES; mock mode and any selector failure fall back to
    # deterministic keyword overlap. The company profile (_profile.md) is ALWAYS
    # included first as identity context, outside the MAX_SELECTED_NOTES budget.

write_back(company_id: str, decision: Decision,
           recommendation: BoardRecommendation, learnings: list[str],
           profile: Optional[CompanyProfile] = None) -> str
    # Appends a decision note + updates the index. This is also the outcome loop:
    # a later outcome is written back against the same decision note.
    # Amendment: returns the decision_id the outcome loop addresses (not None).
    # Amendment: when profile is passed, it is persisted as _profile.md — created
    # on the company's first write, rewritten only when fields change. The note
    # sits on the underscore (skipped) side of the index: never ranked by the
    # selector, loaded explicitly by read().

read_profile(company_id: str) -> Optional[CompanyProfile]
    # Amendment (new export): parses _profile.md back into a CompanyProfile —
    # the hydration source for requests that omit the profile.

# Vault index the selection step reads (one entry per note):
VaultNote:
    path:        str          # filename within the company's vault folder
    frontmatter: dict         # e.g. {type, decision_id, date, recommendation, outcome}
    summary:     str          # one line, so the selector can rank without reading the body

ContextBundle:
    notes:       list[str]    # bodies of the selected notes only
    used_paths:  list[str]    # provenance — which notes informed this run
```

**Amendment — input hardening (recorded):** the contract shapes are unchanged, but the backend
now enforces limits on them: `CompanyProfile` fields carry Pydantic `max_length` caps
(company_name 100 · sector 200 · stage 100 · business_model 200 · size_band 50), `Decision.question`
caps at 500 and `context` at 2000, and `company_id` must match `^[a-z0-9][a-z0-9\-_]{0,49}$`.
`Vault._company_dir` independently validates the id and blocks path traversal outside the vault
root. `/api/analyze` is rate-limited (`ANALYZE_RATE_LIMIT`, default `5/minute`; `RATE_LIMIT_ENABLED`
kills it for tests) — all env-tunable. The frontend mirrors the caps in `types.ts` (`PROFILE_LIMITS`
/ `DECISION_LIMITS`) and as intake `maxLength`s, and `slugId` caps at 50 so a long company name
cannot 422.

**Amendment — hydration is live:** `AnalyzeRequest.profile` is now truly optional: `profile=None`
hydrates the profile from the company's `_profile.md` via `read_profile`; if no stored profile
exists the API returns **422** with a clear message. The old minimal-placeholder branch is gone.

### Canonical agent-name strings

The **same string** must be used for the roster, the agent `name`/`agent_name` attribute, the
LangGraph node key, and the VP summary key. Renaming an agent touches both lanes — freeze these
with the contract:

```
scout · trend · finance · growth · skeptic · capability · venture_partner
```

- `capability` **was `founder_fit`** — rebuilt from "does this *person* fit this idea" into
  "does this *organization* have the capability/readiness to execute this decision."
- The canonical string `venture_partner` **displays as "Chair"** (the board's chair — final
  synthesis). **The string never changes** — `venture_partner` stays in the roster, the
  `agent_name`/`name` attribute, the LangGraph node key, and the VP summary key. Only the
  human-facing label is **"Chair"** (settled).

---

## The seven agents (company-centric)

Each agent is a Python class extending `BaseAgent`. The class scaffolding is unchanged; the
`SYSTEM_PROMPT`, mock fixture, and the shared profile formatter are re-pointed at a company +
decision. Every agent still ends its system prompt with **"Respond with valid JSON only."**

| Agent (`name` string) | New company-centric role |
|---|---|
| Opportunity Scout (`scout`) | Frames the **options on the table** for the decision (generates them only if `decision.options` is empty). Not greenfield idea-hunting. |
| Trend Analyst (`trend`) | Reads market/demand signals **for this decision** (with MCP live data where available). |
| Finance Agent (`finance`) | Models the decision against the **company's** economics (P&L, unit economics, the budget constraint) — not a personal SGD budget. |
| Growth Agent (`growth`) | How the company **executes/goes to market** on the chosen option. |
| Skeptic Agent (`skeptic`) | **The main event.** Attacks the decision's weakest assumptions and most likely failure modes. |
| Capability Agent (`capability`) | **Rebuilt from `founder_fit`.** Scores the **organization's** capability/readiness to execute — team, ops, track record — not a person's skills. |
| Chair (`venture_partner`) | Synthesizes the debate into the board memo (`BoardRecommendation`), incorporating the vault context and the dissent record. **Displays as "Chair"; canonical string stays `venture_partner`.** |

> **`founder_fit → capability` is the highest-churn rename.** It ripples beyond the agent file:
> the VP's `_compile_agent_summary` key, `StartupCard`'s founder-fit score field, and
> `planMarkdown.ts`'s "Founder fit" line all reference it today. Track it as one change set.

---

## Debate Engine (unchanged mechanism, new centrality)

```
Step 1  Conflict Detection   agent_outputs → detect_conflicts() → [ConflictPoint]
Step 2  Debate Rounds (≤3)   per round: agents argue, revise, moderator rules per conflict
Step 3  Consensus Scoring    severity-weighted resolution rate → ConsensusReport
Step 4  Dissent record       unresolved conflicts + final positions → BoardRecommendation.dissent
Step 5  Chair synthesis      the Chair (venture_partner) writes the memo
```

The scoring semantics are unchanged (a *resolution rate*, not idea quality). What changes is that
**unresolved conflicts are a feature of the output**, not a failure — they become the auditable
`dissent[]` and feed `what_would_change_this_call`.

---

## Memory Architecture — vault only

> **Active persistence is the per-company Obsidian markdown vault.** The Postgres modules
> (`episodic.py`/`semantic.py`) and the in-process `store.py` are **not** on the path for the
> pivot. There is no SQLite.

### Flow

```
Decision arrives
      │
      ▼
 vault.read(company_id, query)      # LLM selects relevant notes from the index
      │                             #   (selective retrieval — never the whole vault)
      ▼
 ContextBundle → threaded into the agent society (Chair especially)
      │
      ▼
 Board memo produced
      │
      ▼
 vault.write_back(company_id, decision, recommendation, learnings)
      │                             # new decision note + index update
      ▼
 (later) outcome written back against the same decision note   # the validation loop
```

### Why a vault (not a DB, not RAG)

- **Human-readable + portable** — a company's decision history is plain markdown the operator can
  read and edit.
- **Selective retrieval keeps context small** — the LLM reads a tiny index (frontmatter + filename
  + one-line summary) and pulls only the notes it needs, so context never balloons.
- **Compounds over time** — by session 50 the Chair can retrieve "last time you weighed expansion,
  here's what the Skeptic flagged and what actually happened."

---

## Trust posture

This is advice attached to real money, so the memo is explicit about the limits of its own
confidence:

- **`missing_inputs[]`** — what the council would need to be more sure (never pretends completeness).
- **`what_would_change_this_call`** — the conditions under which the recommendation flips.
- **`dissent[]`** — the objections that did *not* get resolved, attributed by agent.
- **`disclaimer`** — one line: advisory output, not a fiduciary board; the operator owns the call.

---

## API Architecture

```
POST /api/analyze
  Request:  AnalyzeRequest { company_id, profile?, decision }
  Process:  vault.read → agent society (LangGraph) → debate → Chair memo → vault.write_back
  Response: BoardResponse

GET  /api/response/{response_id}
  Response: BoardResponse (from store)

POST /api/feedback         # the outcome loop
  Request:  { response_id, outcome, notes }
  Process:  vault.write_back appends the outcome against the decision note
  Response: { status: "ok" }

GET  /api/company/{company_id}
  Response: the company's decision history (from the vault index)
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM | Qwen (qwen-turbo / qwen-plus via DashScope) | Strong reasoning, JSON mode, cost-effective |
| Framework | FastAPI | Async, auto-docs, Pydantic native |
| Orchestration | LangGraph (StateGraph) | Parallel analyst fan-out via asyncio.gather + to_thread |
| Memory | Per-company Obsidian markdown vault | Human-readable, portable, selective retrieval — no DB/RAG this phase |
| Retrieval | LLM-driven note selection over a small index | No embeddings/vector DB; index = frontmatter + filename + one-line summary |
| Auth | Stubbed company picker → vault folder | Real auth deferred |
| Frontend | Next.js 14 + Tailwind | App Router, TypeScript, fast dev |
| Deployment | Vercel Hobby (FE) + Hugging Face Spaces / Docker (BE) | Long-running container holds the 90–240s debate run; both free, no card (see § Deployment) |

---

## Deployment (Decision #8)

**Backend → Hugging Face Spaces (Docker SDK, free CPU Basic: 2 vCPU / 16 GB RAM).**
Why a long-running container and not serverless: the full 7-agent debate takes **~90–240s per run**.
HF Spaces runs a persistent container with **no per-request function timeout**, so a 240s run
completes. This is *why we do not use Vercel for the backend* — serverless function timeouts can't
hold a 240s run, and the ephemeral serverless filesystem can't hold the vault's markdown
write-back. It is also *why we do not use Railway or Render* — both gate the usable tier behind
payment; HF free CPU Basic needs **no card and no trial clock**. The container listens on **port
7860** (HF Docker default) and runs uvicorn.

**Frontend → Vercel Hobby (Next.js).** Unchanged. Reads the backend base URL from
`NEXT_PUBLIC_API_BASE_URL` — never hardcoded.

**Dev / demo alternative:** run the backend locally and expose it with a **Cloudflare Tunnel** (or
ngrok) to a public URL. Same code, different host — the low-setup option for a live demo when a
laptop can stay on. Point the frontend's `NEXT_PUBLIC_API_BASE_URL` at the tunnel URL.

### Env-var contract (additive to the frozen Phase 0 contract — document, don't implement)

**Backend**

| Var | Purpose |
|---|---|
| `VAULT_PATH` | Filesystem root of the per-company vault. **Env-configurable, never hardcoded** (e.g. `/app/vault` for the baked seed on the Space and locally). |
| `ALLOWED_ORIGINS` | CORS allow-list — the Vercel domain + `http://localhost:3000`. |
| `QWEN_API_KEY` | Existing. DashScope key (empty → mock mode). |
| `USE_MOCK_LLM` | Existing. `true` runs keyless with mock fixtures. |
| *(port)* | Container listens on **7860** (HF Docker default). |

**Frontend**

| Var | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL — the HF Space URL, the tunnel URL, or `http://localhost:8000` in dev. The frontend **must** read the backend base URL from this and never hardcode it. |

**Ownership:** **Lane A** owns `VAULT_PATH` + `ALLOWED_ORIGINS` + the Dockerfile; **Lane B** owns
`NEXT_PUBLIC_API_BASE_URL` wiring. Both lanes depend on this contract → it is on the shared-file
watchlist in `CLAUDE.md`.

### Vault persistence posture on the free tier

The HF free-tier container filesystem (including `/data`) is **ephemeral**. This is acceptable for
the hackathon: a demo runs inside **one live instance**, so `write_back` persists **within the
session**; only a restart/redeploy resets it — which we don't do mid-demo. To make "a returning
company that remembers" work out of the box, a **seed vault** (a couple of sample company folders
with `.md` history) is **baked into the image at build time**.

Because `VAULT_PATH` is env-driven, **path is configuration**: the same code points at the baked
seed on the Space, a local folder in dev, or (future) a synced location — with no code change.

> **Future-only (not this phase):** for cross-restart persistence, push the vault to a **HF Dataset
> repo** via the `huggingface_hub` library. **Do not reintroduce Postgres** — vault-only stands
> (Decision #1).

Full setup steps + the Dockerfile spec live in `docs/deployment.md`.

---

## Lane split & shared files

- **Lane A = `backend/`** (incl. the vault interface + agents + graph + contract in `models.py`).
- **Lane B = `frontend/`** (studio UI, roster, landing copy).

Shared / freeze-first files: `backend/models.py` (Lane A owns, Lane B mirrors),
`frontend/src/components/agentRoster.tsx` (Lane B single-owner; agent-name strings must match
the canonical list above), `frontend/src/app/globals.css` + `tailwind.config.js` (Lane B
single-owner). One owner per doc. The **deployment env-var contract** is shared too: Lane A owns
`VAULT_PATH` + `ALLOWED_ORIGINS` + the Dockerfile; Lane B owns `NEXT_PUBLIC_API_BASE_URL` wiring
(see [§ Deployment](#deployment-decision-8)). See `CLAUDE.md` for the full watchlist.
