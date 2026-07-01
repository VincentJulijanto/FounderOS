# FounderOS — Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what we're building now, what's decided, what's built, what's changing, and
> what to do next. Read this first at the start of any new session. The **canonical, frozen Phase 0
> contract** lives in `docs/architecture.md`; the **standing brief** for both build lanes is `CLAUDE.md`.

**Last updated:** 2026-07-01
**Current phase:** **Phase 1 — Docs & copy pass for the pivot** (this session). Docs/copy only; no
code. Contract drafted into `docs/architecture.md` and awaiting owner sign-off before it freezes.
**Branch:** `phase-1-docs-pivot` (off `main` @ a4e4633). Not committed/pushed — owner squash-merges
after sign-off.

---

## The pivot

FounderOS is moving from **"aspiring founder: profile → startup idea"** (a *generator*) to an
**AI board/council that helps operators of EXISTING businesses evaluate a specific decision** —
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

- **Lane A = `backend/`** — models/contract, agents, graph, and the new vault interface.
- **Lane B = `frontend/`** — studio UI, roster, landing copy.
- Shared/freeze-first files and conventions: see `CLAUDE.md`.

### Highest-churn rename to watch

`founder_fit → capability` (organizational capability/readiness fit). Ripples to the VP summary
key, `StartupCard`'s founder-fit field, and `planMarkdown.ts`. Track as one change set.

---

## What this session (Phase 1) changed — docs & copy only

- **`docs/architecture.md`** — rewritten: generator→evaluator pivot; company-centric agent roles;
  vault-only persistence with LLM-driven selective retrieval + write-back; the **frozen Phase 0 I/O
  contract**; stubbed company picker; trust posture. Flags `founder_fit→capability` as highest-churn
  and the `venture_partner` display label — **since resolved: displays as "Chair"** (canonical
  string stays `venture_partner`).
- **`PROJECT_STATE.md`** (this file) — rewritten to the pivot state; drift fixed (below).
- **`docs/demo_script.md`** — reframed founder→company-decision, ending in a board memo; 6-vs-7
  agent drift fixed (7 canonical everywhere).
- **`README.md`** — reframed from "AI venture studio for founders" to board/council for operators.
- **`CLAUDE.md`** — **created** (none existed). Standing brief: pivot summary, the decisions,
  contract summary, canonical agent-name strings, lane split, shared-file watchlist, conventions.
- **Landing marketing copy** (`frontend/src/components/landing/*`, `Footer.tsx`) — pivot-conflicting
  copy strings rewritten to the board/decision framing (Hero, FeatureCards, HowItWorks, StatsBand,
  Testimonials, FAQ, ClosingCTA, Footer, AgentActivityMockup). **Copy strings only — no structural
  or logic changes.** ProfileForm / ExecutionPlan / studio were NOT touched (separate Lane B build).

### Deployment docs pass (follow-up, same branch)

- **Decision #8 recorded** across `docs/architecture.md` (new **Deployment** section + env-var
  contract), this file, and `CLAUDE.md`.
- **`docs/deployment.md`** — **created**: the single deployment reference both lanes read (HF Space
  setup, Dockerfile spec as prose only, env vars + CORS, local + Cloudflare Tunnel/ngrok, Vercel).
- **`README.md`** — hosting mention corrected (no Railway) + a "Deploying" pointer to `deployment.md`.
- Swept all docs for `Railway`/`Render` — corrected the one stale reference (architecture.md tech
  table). `docs/demo_script.md` has no host/URL reference, so it was left unchanged.

### Drift corrected this session

- **Branch guidance was stale:** the old state said `phase-6-mcp` was "not yet merged — do not
  merge to main." It **is** merged — `main` @ a4e4633 contains the MCP client (`backend/mcp/client.py`)
  and the Sprint B live-mode fixes. Corrected.
- **"SQLite for Phase 5 dev" removed:** no SQLite exists anywhere. Active (pre-pivot) memory was an
  in-process dict (`store.py`); the unwired production schema is **Postgres**. Under the pivot,
  persistence is the **vault** — none of these three are on the path.
- **6-vs-7 agents:** `demo_script.md` opening + Step 2 said "six agents" while the rest said 7. Now
  **7 canonical everywhere**: Scout, Trend, Finance, Growth, Skeptic, **Capability**, Chair
  (display label; canonical string `venture_partner`).

---

## What exists in `main` today (pre-pivot machinery to carry over)

- **Agent society (LangGraph):** `scout → (trend ∥ finance ∥ growth) → skeptic → founder_fit →
  debate → venture_partner`, in `backend/graph.py`. Parallel analyst fan-out via
  `asyncio.gather(asyncio.to_thread(...))`.
- **Debate engine:** `backend/consensus/debate_engine.py` — conflict detection, ≤3 rounds,
  severity-weighted consensus scoring, structured unresolved-conflict output. **Reused as-is** in
  shape; becomes the centerpiece.
- **QwenProvider:** `backend/llm/provider.py` — qwen-turbo/qwen-plus via DashScope, JSON-mode,
  3-attempt retry, in-process cache (hashes the full prompt), mock fallback.
- **MCP client:** `backend/mcp/client.py` — `search_crunchbase`/`search_web`/`fetch_news`,
  mock+live, never crashes the pipeline. `mcp_used`/`mcp_sources` surfaced on the response.
- **Frontend:** Next.js 14 landing + `/studio` app (ProfileForm → AgentDebate → StartupCard →
  ExecutionPlan → CouncilReasoning). Wired to real `/api/analyze` data.
- **Tests:** 44/44 passing pre-pivot, hermetic via `backend/tests/conftest.py` (pins mock mode).

> These will be **reframed/rebuilt** under the pivot (see the touch-map in the recon and the agent
> table in `docs/architecture.md`). Of note: **~5 of 7 agents are rewrites, not re-prompts**, the
> intake fields change, memory is replaced by the vault, and the output model changes.

---

## What's NOT built yet (the pivot work)

- **Vault layer** (`read`/`write_back` + index) — new, on the critical path (Lane A). Signatures
  are frozen in the contract; implementation is a later phase.
- **`models.py` rewrite** — `CompanyProfile`/`Decision`/`AnalyzeRequest` in, **`BoardResponse`
  (wrapping `recommendation: BoardRecommendation`) out**. Freeze-first shared file.
- **Agent reframing/rebuild** — 5 of 7 agents (Scout, Finance, Capability rebuilt; Trend, Growth,
  Skeptic reframed; VP reframed to write the memo).
- **Stubbed company picker** + studio rebuild for decision intake → board memo (Lane B).
- **Landing structural rework** beyond copy (mockups, ProfileForm) — later Lane B.

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
2. **Getting the contract signed off / frozen** — it is the gate for both lanes.
3. Once frozen: Lane A implements `models.py` to match, then the vault interface; Lane B mirrors
   the models in `studio/page.tsx` and starts the company picker + decision intake. **Do not start
   agent/UI logic before the contract is frozen.**
4. (Resolved) `venture_partner` displays as **Chair**; canonical string unchanged. Naming target
   for the app surface is **"boardroom"** — the `/studio`→`/boardroom` rename + copy sweep is Lane
   B's rebuild (one commit), not a docs task.
