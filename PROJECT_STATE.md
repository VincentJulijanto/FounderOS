# FounderOS: Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what we're building now, what's decided, what's built, what's changing, and
> what to do next. Read this first at the start of any new session. The **canonical, frozen Phase 0
> contract** lives in `docs/architecture.md`; the **standing brief** for both build lanes is `CLAUDE.md`.

**Last updated:** 2026-07-14
**Current phase:** **SUBMISSION-READY — All Track 3 features merged and live. Submission checklist items complete.**
Everything through PR #18 is merged to `main` and deployed: frontend at **founderos-zeta.vercel.app**
(Vercel Hobby), backend at **vincent-playground-founderos-api.hf.space** (HF Docker Space, CPU Basic, live Qwen).
- **Live-validated end to end:** three full runs through the HF proxy (93s / 132s / 100s, all
  HTTP 200, zero parse failures on the raised token ceilings). The **MVP loop is proven live**:
  cold-start company typed fresh → live board run → `_profile.md` + decision note written →
  second run hydrates the profile (`profile=None` → 200) and the memo cites the prior decision.
- **Shipped to `main` (PRs #10–#12):** live-run fixes (anti-invention prompts, debate 6000-token
  ceiling, round-2 stalemate grace, ~110s wait pacing, slug word-boundary) · vault profile
  persistence + hydration (PR #10) · "Board memory consulted" provenance line (PR #11) · PDF
  export + security hardening (PR #12).
- **On `feat/research-agent` (not yet merged to `main`):** memo legibility + strip markdown
  emphasis markers (#14) · memo legibility final polish (#15) · memo narrative thread — summary on
  top, WHY/WHAT/HOW breakdown (#16) · **Market Intelligence (`research`) agent** — `MarketResearchAgent`
  in `backend/agents/research.py`; fetches real-world benchmarks (web/news/crunchbase) via MCP
  after Scout and before the analyst fan-out; injects `research_brief` into every analyst's
  context; `BoardResponse.research_sources` added; graph rewired `scout → research → analysts`;
  `docs/agent-research.md` design spec shipped with the implementation.
**Research agent:** merged to `main` via Vincent's PR #17. Branches `feat/research-agent` and
`docs/research-agent-update` deleted (superseded).

**Feedback Intelligence Council:** merged to `main` via PR #18. 3-agent sub-council (Analyst →
Skeptic → Chair) for Track 3: Agent Society. 9 hermetic tests passing.

**Submission prep (2026-07-14 session):**
- `LICENSE` (MIT) added to repo root — satisfies hackathon open-source requirement
- `frontend/src/app/boardroom/council/page.tsx` — new Feedback Council UI page (Track 3 demo)
- `frontend/src/components/CouncilBrief.tsx` — council dialogue + efficiency gain + theme ranking
- Types added to `frontend/src/lib/types.ts`: `CouncilTurn`, `FeedbackTheme`, `BaselineComparison`, `CouncilBriefResponse`
- Boardroom header now links to `/boardroom/council` (Feedback Council)
- `docs/architecture-diagram.md` — Mermaid system diagram (two-layer agent society, required by hackathon)
- `README.md` rewritten around Track 3 submission narrative; cross-track elements (Track 1 memory, Track 4 autopilot) explicit; license badge added

**Remaining before July 20:**
- Rehearse the 3-minute demo with a stopwatch per `docs/demo_script.md`
- Archive Kestrel cold-start receipt
- Deploy frontend (Vercel) + backend (HF Space) with latest `main`
- Record 3-minute YouTube/Vimeo demo video (required)
- Submit at devpost with GitHub link, video, architecture diagram, track = Track 3
- **Optional (blog post award +$500):** technical writeup and publish link

---

## Build Tracker (live)

The single live home for where we are, whose job each piece is, and by when. The spine is the
9-day schedule. Owners: **Vincent** (frontend / Lane B), **Steven** (backend / Lane A, owns the vault
by default), or **Joint**.

| Day | Focus | Owner | Status |
|---|---|---|---|
| Day 1 | Phase 0: freeze contract (Pydantic I/O + vault interface signatures + agent-name strings) and finish docs pivot | Joint | Docs done; contract implemented in `models.py` (Phase 2) |
| Day 2-3 | Vincent: company/decision intake rebuild + board-memo renderer scaffold vs mock fixtures. Steven: vault module (read/retrieval/write-back) + agent rebuilds (scout, finance, capability) | Split | **Steven: DONE.** **Vincent: DONE** (intake + memo renderer, Phase 5) |
| Day 4-5 | Vincent: ExecutionPlan to board-memo sections, planMarkdown in lockstep, studio TS interfaces. Steven: graph rewire, Chair (venture_partner) synthesis, reframes (trend, growth, skeptic) | Split | **Steven: DONE.** **Vincent: DONE** (phased plan in BoardMemo, planMarkdown rewritten, TS mirror in Phase 4) |
| Day 6 | Vincent: landing + agentRoster. Steven: main.py endpoints, wire vault into the run, tests. (Backend assist window if Vincent is free) | Split | **Steven: DONE.** **Vincent: DONE** (roster to canonical strings Phase 4; landing CTAs + copy sweep Phase 6) |
| Day 6.5 | Steven: Decision #8 deploy wiring — Dockerfile + `.dockerignore` + Space README + seed vault | Steven (Lane A) | **DONE** (Phase 3, `phase-3-deployment`) |
| Day 6.6 | Lane B frontend pivot: contract mirror + roster (P4), evaluator app intake + memo (P5), `/studio → /boardroom` rename + copy sweep (P6) | Lane B | **DONE** (Phases 4–6) |
| Day 7 | Buffer / MCP connector stretch. Vincent: renderer polish. Steven: Xero or Shopify into Finance if ahead | Split | **DONE** (P9 book-financials connector, mock-safe; live-run fix pass PR #9) |
| Day 8 | Integration: real backend to real frontend, fix drift. Feature freeze end of day | Joint | **DONE** — deployed (HF Space + Vercel), 3 live proxy runs green, profile persistence + provenance + PDF export shipped (PRs #10–#12). **Feature freeze in effect.** |
| Day 9 | Demo prep + buffer | Joint | **In progress** — script v2 locked (`docs/demo_script.md`); Research agent added (feat/research-agent); remaining: merge branches, Kestrel receipt archival, stopwatch rehearsals |

The canonical lane/ownership split and shared-file watchlist already live in this file (below) and
in `CLAUDE.md`; update the **Status** column as work lands. The rows map onto the blueprint's build
phases (`docs/blueprint.html` §6): its **Memory Loop** phase, for instance, is the vault, built on
Day 2-3. The schedule here stays the spine; do not duplicate this table into the blueprint.

---

## The pivot

FounderOS is moving from **"aspiring founder: profile → startup idea"** (a *generator*) to an
**AI board/council that helps operators of EXISTING businesses evaluate a specific decision**:
"is this sound, and what's missing?" (an *evaluator*). Output is a **board-ready memo**. Company
context persists as a **per-company Obsidian markdown vault** with selective retrieval + write-back,
so the council remembers across sessions without loading everything into context. The 8-agent
debate machinery carries over; **inputs, agent framing, memory, and output format change**, and the
**Skeptic + Debate Engine become the main event**.

### The eight decisions (settled)

1. **Persistence: vault only.** Postgres (`episodic.py`/`semantic.py`) stays unwired/out of the
   path. **No SQLite** (that note was drift).
2. **Retrieval: LLM-driven note selection** over a small vault index. No embeddings/RAG/vector DB.
3. **Auth: stubbed** company picker → vault folder.
4. **Input unit: evaluator, one decision per run.** Not idea-generation, not periodic review.
5. **Outcome/validation loop: folded into vault write-back.** Memo carries the trust posture.
6. **Name: keep "FounderOS."**
7. **Register: board-memo structure, plain operator language** (no consultant/McKinsey jargon).
8. **Deployment: HF Spaces (Docker) for the backend, Vercel Hobby for the frontend.** A
   long-running container holds the ~90–240s debate run that serverless can't, and both tiers are
   free with no card (not Railway/Render, which paywall the usable tier). Vault path is config;
   free-tier filesystem is ephemeral (fine for a demo) with a seed vault baked into the image.

Full contract + agent roles: `docs/architecture.md`. Deployment reference: `docs/deployment.md`.

### Lane split

- **Lane A = `backend/`** (Steven): models/contract, agents, graph, and the new vault interface.
- **Lane B = `frontend/`** (Vincent): studio UI, roster, landing copy.
- Shared/freeze-first files and conventions: see `CLAUDE.md`.

### Highest-churn rename to watch

`founder_fit → capability` (organizational capability/readiness fit). Ripples to the VP summary
key, `StartupCard`'s founder-fit field, and `planMarkdown.ts`. Track as one change set.

---

## What this session (Phase 1) changed: docs & copy only

- **`docs/architecture.md`**, rewritten: generator→evaluator pivot; company-centric agent roles;
  vault-only persistence with LLM-driven selective retrieval + write-back; the **frozen Phase 0 I/O
  contract**; stubbed company picker; trust posture. Flags `founder_fit→capability` as highest-churn
  and the `venture_partner` display label, **since resolved: displays as "Chair"** (canonical
  string stays `venture_partner`).
- **`PROJECT_STATE.md`** (this file), rewritten to the pivot state; drift fixed (below).
- **`docs/demo_script.md`**, reframed founder→company-decision, ending in a board memo; 6-vs-7
  agent drift fixed (7 canonical everywhere).
- **`README.md`**, reframed from "AI venture studio for founders" to board/council for operators.
- **`CLAUDE.md`**, **created** (none existed). Standing brief: pivot summary, the decisions,
  contract summary, canonical agent-name strings, lane split, shared-file watchlist, conventions.
- **Landing marketing copy** (`frontend/src/components/landing/*`, `Footer.tsx`): pivot-conflicting
  copy strings rewritten to the board/decision framing (Hero, FeatureCards, HowItWorks, StatsBand,
  Testimonials, FAQ, ClosingCTA, Footer, AgentActivityMockup). **Copy strings only, no structural
  or logic changes.** ProfileForm / ExecutionPlan / studio were NOT touched (separate Lane B build).

### Deployment docs pass (follow-up, same branch)

- **Decision #8 recorded** across `docs/architecture.md` (new **Deployment** section + env-var
  contract), this file, and `CLAUDE.md`.
- **`docs/deployment.md`**, **created**: the single deployment reference both lanes read (HF Space
  setup, Dockerfile spec as prose only, env vars + CORS, local + Cloudflare Tunnel/ngrok, Vercel).
- **`README.md`**, hosting mention corrected (no Railway) + a "Deploying" pointer to `deployment.md`.
- Swept all docs for `Railway`/`Render`; corrected the one stale reference (architecture.md tech
  table). `docs/demo_script.md` has no host/URL reference, so it was left unchanged.

### Drift corrected this session

- **Branch guidance was stale:** the old state said `phase-6-mcp` was "not yet merged; do not
  merge to main." It **is** merged: `main` @ a4e4633 contains the MCP client (`backend/mcp/client.py`)
  and the Sprint B live-mode fixes. Corrected.
- **"SQLite for Phase 5 dev" removed:** no SQLite exists anywhere. Active (pre-pivot) memory was an
  in-process dict (`store.py`); the unwired production schema is **Postgres**. Under the pivot,
  persistence is the **vault**; none of these three are on the path.
- **6-vs-7 agents:** `demo_script.md` opening + Step 2 said "six agents" while the rest said 7. Now
  **7 canonical everywhere**: Scout, Trend, Finance, Growth, Skeptic, **Capability**, Chair
  (display label; canonical string `venture_partner`).

---

## What exists in `main` today (pre-pivot machinery to carry over)

- **Agent society (LangGraph):** `scout → (trend ∥ finance ∥ growth) → skeptic → founder_fit →
  debate → venture_partner`, in `backend/graph.py`. Parallel analyst fan-out via
  `asyncio.gather(asyncio.to_thread(...))`.
- **Debate engine:** `backend/consensus/debate_engine.py`, conflict detection, ≤3 rounds,
  severity-weighted consensus scoring, structured unresolved-conflict output. **Reused as-is** in
  shape; becomes the centerpiece.
- **QwenProvider:** `backend/llm/provider.py`, qwen-turbo/qwen-plus via DashScope, JSON-mode,
  3-attempt retry, in-process cache (hashes the full prompt), mock fallback.
- **MCP client:** `backend/mcp/client.py`, `search_crunchbase`/`search_web`/`fetch_news`,
  mock+live, never crashes the pipeline. `mcp_used`/`mcp_sources` surfaced on the response.
- **Frontend:** Next.js 14 landing + `/studio` app (ProfileForm → AgentDebate → StartupCard →
  ExecutionPlan → CouncilReasoning). Wired to real `/api/analyze` data.
- **Tests:** 44/44 passing pre-pivot, hermetic via `backend/tests/conftest.py` (pins mock mode).

> These will be **reframed/rebuilt** under the pivot (see the touch-map in the recon and the agent
> table in `docs/architecture.md`). Of note: **~5 of 7 agents are rewrites, not re-prompts**, the
> intake fields change, memory is replaced by the vault, and the output model changes.

---

## What Phase 2 (this session) built — Lane A backend pivot

All backend code adapted to the evaluator/board contract; **`python -m pytest -q` → 30 passed**,
hermetic mock mode. Machinery reframed in place (debate engine, provider, MCP, LangGraph
structure preserved), not rewritten from scratch.

- **`backend/models.py`** — rewritten to the frozen contract: `CompanyProfile`/`Financials`/
  `Decision`/`Constraints`/`AnalyzeRequest` in; `BoardResponse` wrapping `BoardRecommendation`
  (with `OptionAssessment`, `Dissent`, phased `ExecutionPlan`/`Phase`) out; vault models
  (`VaultNote`, `ContextBundle`). `AgentOutput`/`ConflictPoint`/`DebateRound`/`ConsensusReport`
  carried over unchanged. Old `UserProfile`/`StartupIdea`/`LeanCanvas`/`VentureRecommendation`
  removed. Live-LLM coercion validators retained + extended (recommendation/confidence coercion).
- **`backend/vault/`** — NEW, on the critical path. File-backed per-company markdown vault under
  `VAULT_PATH`. `read(company_id, query) → ContextBundle` (selective retrieval: LLM note-selection
  in live mode, keyword-overlap fallback in mock; caps at 4 notes), `write_back(...)` (appends a
  decision note + frontmatter index), `record_outcome(...)` (the outcome loop), `history(...)`.
- **Agents (all 7, canonical `name` strings)** — `scout` frames options; `trend`/`finance`/
  `growth` reframed company/decision-centric; `skeptic` is the main event (attacks the decision);
  **`founder_fit → capability`** rebuilt (org readiness, 5 new dimensions) — old file deleted;
  `venture_partner` (Chair) writes the `BoardRecommendation`, deriving `dissent[]` from the
  debate's unresolved conflicts. `base.py` now formats company + decision (not a founder profile).
- **`backend/graph.py`** — rewired: `scout → analysts (trend ∥ finance ∥ growth ∥ capability) →
  skeptic → debate → venture_partner`. Node keys + `agent_outputs` keys are canonical strings.
  New state (`company_profile`, `decision`, `vault_context`, `recommendation`).
- **`backend/main.py`** — new routes: `POST /api/analyze` (vault.read → board → vault.write_back),
  `GET /api/response/{id}`, `POST /api/feedback` (outcome loop), `GET /api/company/{id}`. Old
  `/api/recommendation` + `/api/memory` retired. Listens on **7860** (HF default).
- **`backend/config.py`** — `vault_path` + `allowed_origins` (Decision #8) added; CORS reads
  `ALLOWED_ORIGINS` then falls back to `cors_origins`.
- **Debate engine** — prompts + mock fixtures reframed to a market-expansion decision with
  canonical agent names; **scoring math unchanged** (worked example still 6.0 / Moderate).
- **Tests** — `test_pipeline.py` + `test_mcp.py` rewritten to the new contract; **`test_vault.py`
  added** (read/write/outcome loop + full HTTP flow); `test_memory.py` deleted (in-process memory
  loop retired — vault replaces it). Shared `company`/`decision` fixtures in `conftest.py`.

## What Phase 3 (this session) built — Lane A deployment wiring (Decision #8)

Suite still green (**30 passed**, mock mode). All additive — no backend logic changed.

- **`Dockerfile`** (repo root) — `python:3.11-slim`; installs `backend/requirements.txt` as a cached
  layer; copies `backend/`; **bakes the seed `vault/` into `/app/vault`**; sets non-secret defaults
  (`VAULT_PATH=/app/vault`, `USE_MOCK_LLM=true`); `EXPOSE 7860`; `CMD uvicorn backend.main:app
  --host 0.0.0.0 --port 7860`. (`backend` is a PEP 420 namespace package — no `__init__.py` needed.)
- **`.dockerignore`** — keeps the image slim (excludes `.git`, `.venv`, `frontend/`, tests, logs).
- **`SPACE_README.md`** (repo root) — the HF Space's own `README.md` with the required frontmatter
  (`sdk: docker`, `app_port: 7860`) + Space secrets/variables table. Distinct from the project README.
- **`vault/`** (repo root, = the `./vault` config default) — the **seed vault**: two sample
  companies with real decision history and recorded outcomes, so "a returning company that
  remembers" works on a cold instance. `harborline-logistics` (3 notes: Vietnam lane, own-fleet,
  cold-chain) + `lumen-skincare` (2 notes: retail, CRM shift). Verified end-to-end against the real
  `Vault` (index → date-sort → selective `read`).
- **`.env.example`** — added `VAULT_PATH` + `ALLOWED_ORIGINS` (Decision #8 env contract).
- **`docs/deployment.md`** — spec note flipped from "not implemented" to "implemented; see `Dockerfile`".

> **Not done in Phase 3:** an actual `docker build` (Docker CLI unavailable in the session) — the
> Dockerfile is validated by inspection + the app boots under the test suite. Build it on a machine
> with Docker before the demo (checklist in `docs/deployment.md`).

## What Phases 4–6 (this session) built — Lane B frontend pivot

Reframe-in-place, not a rewrite: the debate machinery (`AgentDebate`, `CouncilReasoning`), the
design system (`globals.css`, `tailwind.config.js`), landing structure, and `Logo` are all kept;
only the generator-specific surfaces changed. `tsc --noEmit` clean and `next build` green after each
phase. **The full evaluator app works end-to-end against the mock backend.**

- **Phase 4 (`phase-4-frontend-contract`)** — `frontend/src/lib/types.ts` NEW: the TS mirror of
  `backend/models.py` (BoardResponse/BoardRecommendation/AgentOutput/debate + company/decision
  inputs). `agentRoster.tsx` re-keyed on the **canonical strings** with a `label` field
  (`venture_partner` → "Chair"; `founder_fit` → `capability`); company-centric roles; `labelFor`/
  `roleFor` exports. `AgentDebate` + `CouncilReasoning` now match on canonical `agent_name` and
  render labels (they were silently broken against the pivoted backend). **Root cause fixed:** the
  backend emits `scout·trend·…·venture_partner`; the UI had matched on old display names.
- **Phase 5 (`phase-5-frontend-app`)** — `DecisionIntake.tsx` NEW (stubbed company picker seeded with
  `harborline-logistics`/`lumen-skincare` + "new company" → company profile + one decision).
  `BoardMemo.tsx` NEW (verdict + confidence, options assessed, phased plan, dissent, what-would-
  change, financial view, missing inputs, risks, disclaimer). `studio/page.tsx` rebuilt to the
  input→analyzing→debating→results flow posting `{company_id, profile, decision}` to `/api/analyze`
  and reading `BoardResponse`; API base is **`NEXT_PUBLIC_API_BASE_URL`**. `planMarkdown.ts` →
  `memoToMarkdown(BoardResponse)`. Removed `ProfileForm`/`StartupCard`/`ExecutionPlan` (old
  generator UI). **Verified: the exact intake request body round-trips → 200 `BoardResponse`.**
- **Phase 6 (`phase-6-boardroom-rename`)** — `/studio → /boardroom` route move (`git mv`); all CTAs
  (`LandingNav`, `Hero`, `ClosingCTA`, `Footer`) → `/boardroom` + "Enter the boardroom"; `layout.tsx`
  metadata reframed off "Venture Studio"; residual "studio"/"council" copy swept to "boardroom"/
  "board". No `studio` reference remains in `frontend/src`.

## What this session built — Feedback Intelligence Council (Track 3: Agent Society)

Branch: `feat/feedback-council`. **72/72 tests passing.** Two commits:
- `4e6d264` — feat: Feedback Intelligence Council initial implementation
- `bc30de9` — fix: feedback council — 5 bugs from council review

### New files
- **`backend/agents/feedback_analyst.py`** — clusters vault feedback notes into ranked themes + produces single-agent baseline summary
- **`backend/agents/feedback_skeptic.py`** — challenges Analyst themes for survivorship bias, scope creep, thesis misalignment
- **`backend/agents/feedback_chair.py`** — synthesises both sides; explicitly accepts/reframes/overrides each Skeptic challenge
- **`backend/consensus/feedback_council.py`** — orchestrates the three agents sequentially; builds `council_dialogue`, `baseline_comparison`, and `CouncilBriefResponse`
- **`backend/tests/test_feedback_council.py`** — 9 hermetic tests (mock-pinned)
- **`vault/harborline-logistics/feedback-2026-07-09-*.md`** — 3 seed feedback notes (port congestion, customs timeline, software recommendation)

### Models added to `backend/models.py` (additive)
`FeedbackNote`, `FeedbackTheme`, `CouncilTurn`, `BaselineComparison`, `CouncilBriefRequest`, `CouncilBriefResponse`

### Modified files
- **`backend/vault/store.py`** — `read_feedback(company_id)` added; feedback notes excluded from `index()` (prevents them appearing as prior decisions)
- **`backend/vault/__init__.py`** — exports `read_feedback`
- **`backend/agents/__init__.py`** — exports 3 new agent classes
- **`backend/main.py`** — `POST /api/council-brief` endpoint (rate-limited, COUNCIL_RATE_LIMIT env var)
- **`backend/tests/test_system.py`** — updated vault note counts (Indonesia note counted; feedback notes excluded from index)

### Track 3 criterion map
| Criterion | Where it shows |
|---|---|
| Task decomposition + role assignment | 3 agents with distinct system prompts and input shapes |
| Dialogue and negotiation | `council_dialogue: List[CouncilTurn]` — each agent's message is visible |
| Conflict resolution | Chair's `overrides[]` record: accepted / reframed / overridden per Skeptic challenge |
| Measurable efficiency gain | `baseline_comparison.corrections_count` — integer delta, council vs. single agent |

### Bugs fixed (council review → `bc30de9`)
1. Post-hoc `agent.mock = mock` overrides removed (crash: provider.mock desync)
2. Per-agent try/except with inline `AgentOutput` fallback
3. Skeptic dialogue turn now uses `skeptic_out.analysis` (was `analyst_out.analysis`)
4. `run()` accepts `company_id` param; no post-hoc mutation
5. `_derive_corrections`: unaddressed Chair challenges recorded instead of silently dropped
6. Chair `recommendations` filter: `== "reframed"` (was `!= "accepted"`, incorrectly included "overridden")

## What's NOT built yet

- **Real `docker build` + live deploy** (Lane A, from Phase 3) — Docker CLI wasn't available in-session.
- **Live end-to-end frontend↔backend run** — validated via `next build` + a mock-backend contract
  round-trip; not yet run against a live Qwen key or a deployed Space (Day 8 integration).
- **Postgres memory path** stays retired (Decision #1). `backend/memory/` + `benchmark/` remain
  off-path (untouched, don't import the new models).

---

## Conventions to remember

- **LLM is Qwen** (DashScope), not Anthropic. Keyless mock mode must keep working throughout.
- Each agent owns a `SYSTEM_PROMPT` module constant ending **"Respond with valid JSON only."** and a
  `_mock_response()` fixture. `analyze(profile, context)` → `_call_llm` → `_parse_json` → `AgentOutput`.
- Model tiering: reasoning-heavy agents (`skeptic`, `capability`, `venture_partner`) use `DEEP_MODEL`;
  others `FAST_MODEL`. Deep agents need `max_tokens` ≈ 6000 (live JSON truncates at 2000).
- Pydantic **v2** (`model_dump()`, `field_validator(mode="before")` coercion for messy live output).
- `.env` currently boots **live** (`USE_MOCK_LLM=false` + real `QWEN_API_KEY`); set `USE_MOCK_LLM=true`
  to run keyless. A live run is slow (~90–240s).

---

## Next session should start by

1. Reading this file, then `docs/architecture.md` (the contract) and `CLAUDE.md` (the brief).
2. **Merge `feat/feedback-council` → `main`** (squash or regular merge; discuss with Vincent first).
3. **Demo prep:** rehearse the 3-minute demo with a stopwatch per `docs/demo_script.md`; archive
   Kestrel cold-start receipt; morning-of ritual.
4. **Optional:** wire `POST /api/council-brief` to a simple frontend page in the boardroom so
   the Track 3 demo is visually compelling (Vincent's lane).
