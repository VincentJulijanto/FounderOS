# FounderOS: Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what we're building now, what's decided, what's built, what's changing, and
> what to do next. Read this first at the start of any new session. The **canonical, frozen Phase 0
> contract** lives in `docs/architecture.md`; the **standing brief** for both build lanes is `CLAUDE.md`.

**Last updated:** 2026-07-01
**Current phase:** **Phase 2: Backend pivot (Lane A) — contract, vault, agents, graph, API.** Code
adapted to the evaluator/board contract; suite green (30 passed). Old founder-generator machinery
reframed in place, not deleted.
**Branch:** `phase-2-pivot-backend` (off `main` @ afb1839). Not committed/pushed; owner
squash-merges after review.

---

## Build Tracker (live)

The single live home for where we are, whose job each piece is, and by when. The spine is the
9-day schedule. Owners: **Vincent** (frontend / Lane B), **Steven** (backend / Lane A, owns the vault
by default), or **Joint**.

| Day | Focus | Owner | Status |
|---|---|---|---|
| Day 1 | Phase 0: freeze contract (Pydantic I/O + vault interface signatures + agent-name strings) and finish docs pivot | Joint | Docs done; contract implemented in `models.py` (Phase 2) |
| Day 2-3 | Vincent: company/decision intake rebuild + board-memo renderer scaffold vs mock fixtures. Steven: vault module (read/retrieval/write-back) + agent rebuilds (scout, finance, capability) | Split | **Steven: DONE** (vault + scout/finance/capability rebuilt). Vincent: not started |
| Day 4-5 | Vincent: ExecutionPlan to board-memo sections, planMarkdown in lockstep, studio TS interfaces. Steven: graph rewire, Chair (venture_partner) synthesis, reframes (trend, growth, skeptic) | Split | **Steven: DONE** (graph rewired, Chair writes memo, trend/growth/skeptic reframed). Vincent: not started |
| Day 6 | Vincent: landing + agentRoster. Steven: main.py endpoints, wire vault into the run, tests. (Backend assist window if Vincent is free) | Split | **Steven: DONE** (new endpoints, vault wired, tests green). Vincent: not started |
| Day 7 | Buffer / MCP connector stretch. Vincent: renderer polish. Steven: Xero or Shopify into Finance if ahead | Split | Not started |
| Day 8 | Integration: real backend to real frontend, fix drift. Feature freeze end of day | Joint | Not started |
| Day 9 | Demo prep + buffer | Joint | Not started |

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
so the council remembers across sessions without loading everything into context. The 7-agent
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

## What's NOT built yet

- **Seed vault baked into the image** (Decision #8) — a couple of sample company folders with `.md`
  history for the "returning company that remembers" demo. Not created yet.
- **Dockerfile + deployment wiring** (Lane A, Decision #8) — port 7860, `VAULT_PATH`/`ALLOWED_ORIGINS`.
- **Lane B (frontend)** — everything: stubbed company picker, decision intake → board-memo renderer,
  `/studio → /boardroom` rename + copy sweep, roster to canonical strings, mirror `models.py` in TS.
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
2. **Review + squash-merge `phase-2-pivot-backend`** — the backend now implements the frozen
   contract end-to-end with a green suite. The contract in code IS the implementation of §Frozen
   I/O Contract; treat any drift between them as a bug in the code, not the doc.
3. **Lane A remaining:** seed vault (sample company `.md` history) + Dockerfile (port 7860,
   `VAULT_PATH`/`ALLOWED_ORIGINS`) for Decision #8.
4. **Lane B can now start against the real contract:** mirror `backend/models.py` shapes in TS,
   build the stubbed company picker → decision intake → board-memo renderer, do the
   `/studio → /boardroom` rename + copy sweep (one commit), point the roster at the canonical
   strings (`venture_partner` displays as **Chair**). The backend `/api/analyze` returns a real
   `BoardResponse` in mock mode, so Lane B can integrate without a key.
