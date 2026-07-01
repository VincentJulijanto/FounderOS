# FounderOS — contributor brief

Standing brief for every Claude Code session on this repo. Read this, then `docs/architecture.md`
(the frozen contract) and `PROJECT_STATE.md` (current status). **LLM provider is Qwen (DashScope),
not Anthropic.** Keyless mock mode must keep working throughout.

## The pivot (what we're building)

FounderOS is an **AI board/council for operators of existing businesses**. You bring **one
decision** ("is this sound, what are we missing?"); seven agents evaluate + debate it and return a
**board-ready memo**. This is an **evaluator** (converge on a verdict for a given decision), not the
old **generator** (invent startup ideas from a personal profile). The 7-agent debate machinery
carries over; **inputs, agent framing, memory, and output format change**, and the **Skeptic +
Debate Engine are the main event.**

## The eight decisions (settled — build to these)

1. **Persistence: vault only** — per-company Obsidian markdown vault. Postgres (`memory/episodic.py`,
   `semantic.py`) stays **unwired/off the path**. **No SQLite.**
2. **Retrieval: LLM-driven note selection** over a small index (frontmatter + filename + one-line
   summary). No embeddings / RAG / vector DB.
3. **Auth: stubbed** company picker → vault folder.
4. **Input unit: evaluator, one decision per run.**
5. **Outcome loop: folded into vault write-back** (decision → recommendation → later outcome).
6. **Name: keep "FounderOS."**
7. **Register: board-memo structure, plain operator language** — no consultant/McKinsey jargon.
8. **Deployment: HF Spaces (Docker) backend + Vercel Hobby frontend.** Long-running container holds
   the ~90–240s debate (serverless can't); both free, no card (not Railway/Render). Vault path is
   config; free-tier FS is ephemeral (fine for demo) with a seed vault baked into the image. See
   `docs/deployment.md` and `docs/architecture.md` § Deployment.

## Frozen contract (summary — full shapes in `docs/architecture.md`)

- **In:** `AnalyzeRequest { company_id, profile?: CompanyProfile, decision: Decision }`.
  - `CompanyProfile { company_name, sector, stage, business_model, size_band, financials }`
  - `Decision { question, context?, constraints, options? }` (Scout frames options if empty)
  - **Dropped from old intake:** `name`, `weekly_hours`, `skills`.
- **Out:** `BoardResponse` = agent-society envelope (`agent_outputs[]`, `debate_rounds[]`,
  `consensus`, `mcp_used`, `mcp_sources`) **+** `recommendation: BoardRecommendation`.
  - `BoardRecommendation { recommendation: proceed|hold|conditional, confidence: low|medium|high,
    rationale, missing_inputs[], options_assessed[], dissent[]{agent,position},
    what_would_change_this_call, execution_plan(phased), financial_view, risks[], disclaimer }`.
- **Vault (signatures only for now):** `read(company_id, query) -> ContextBundle` (LLM-selected
  notes only) · `write_back(company_id, decision, recommendation, learnings) -> None`.

**The contract is the gate.** Do not start agent or UI logic before it is signed off/frozen.

## Canonical agent-name strings

Use the **same string** for the roster, the agent `name`/`agent_name`, the LangGraph node key, and
the VP summary key:

```
scout · trend · finance · growth · skeptic · capability · venture_partner
```

- `capability` **was `founder_fit`** (rebuilt: organizational capability/readiness, not a person's
  skills). **Highest-churn rename** — also touches the VP `_compile_agent_summary` key,
  `StartupCard`'s founder-fit field, and `planMarkdown.ts`. Do it as one change set.
- `venture_partner` **displays as "Chair"** (settled). The **string never changes** — roster,
  `agent_name`/`name`, graph node key, and VP summary key all stay `venture_partner`; only the
  human-facing label is "Chair".

## App surface naming

- The target term for the app surface is **"boardroom"** (not "studio"). Docs may refer to the app
  as the "boardroom" narratively.
- The **`/studio` → `/boardroom` route rename** and the **studio → boardroom copy sweep** are
  **Lane B's rebuild, shipped as one coherent commit** — NOT a docs pass. Do not rename the route,
  `LandingNav`, Hero/ClosingCTA CTAs, or any route string as part of docs work.

## Lane split

- **Lane A = `backend/`** — `models.py`, agents, `graph.py`, debate engine, the new **vault**
  interface, and the API **route names** (see watchlist). (The vault is on the critical path — do
  not let it hide inside general backend work.)
- **Lane B = `frontend/`** — the app (decision intake → board memo; the "boardroom" surface),
  roster, landing copy.

## Shared-file watchlist (coordinate — don't parallel-edit)

| File | Owner | Rule |
|---|---|---|
| `backend/models.py` | **Lane A owns**, Lane B mirrors | Freeze first. Lane B mirrors it in `frontend/src/app/studio/page.tsx`. |
| `frontend/src/components/agentRoster.tsx` | **Lane B single-owner** | Source of truth for agent display; names must match the canonical strings above. |
| `frontend/src/app/globals.css` | **Lane B single-owner** | Design tokens; high merge-conflict risk. |
| `frontend/tailwind.config.js` | **Lane B single-owner** | Same. |
| `Dockerfile` + `VAULT_PATH` + `ALLOWED_ORIGINS` | **Lane A owns** | Deploy config (Decision #8). Container listens on `7860`; bakes the seed vault into the image; both vars are env-driven, never hardcoded. |
| `NEXT_PUBLIC_API_BASE_URL` (frontend env) | **Lane B owns** | Backend base URL — read from env, never hardcode the backend URL. |
| API route names | **Lane A owns** | `/api/analyze`, `/api/response/{id}`, `/api/company/{company_id}`, `/api/feedback`. Response body is `BoardResponse`. Old `/api/recommendation` + `/api/memory/{user_id}` are retired. |
| Docs (`architecture.md`, `PROJECT_STATE.md`, `demo_script.md`, `deployment.md`, `README.md`, this file) | **One owner per doc** | Announce before editing a doc the other lane depends on. |

## Env-var contract (Decision #8 — additive to the frozen Phase 0 contract)

- **Backend:** `VAULT_PATH` (vault root, e.g. `/app/vault`), `ALLOWED_ORIGINS` (CORS: Vercel domain
  + `http://localhost:3000`), plus existing `QWEN_API_KEY` / `USE_MOCK_LLM`. Container listens on
  **port 7860** (HF Docker default).
- **Frontend:** `NEXT_PUBLIC_API_BASE_URL` (HF Space URL / tunnel URL / `http://localhost:8000`).
- Full deployment reference: `docs/deployment.md`. Do not reintroduce Postgres — vault-only stands.

## Conventions

- **Pydantic v2** — `model_dump()` (not `.dict()`); use `field_validator(mode="before")` to coerce
  messy live-LLM output (lists/dicts/`"8/10"` strings) into declared shapes.
- **Every agent `SYSTEM_PROMPT` ends with "Respond with valid JSON only."** Each agent owns a
  `_mock_response()` fixture; keyless mock mode must keep passing.
- **Model tiering + max_tokens:** reasoning-heavy agents (`skeptic`, `capability`, `venture_partner`)
  use `DEEP_MODEL` with `max_tokens` ≈ **6000** (live JSON truncates at the old 2000 ceiling);
  others use `FAST_MODEL`. Set `max_tokens` per agent class, not globally.
- **Provider:** `QwenProvider` (DashScope, JSON mode, 3-attempt retry, full-prompt cache key). Never
  call `.chat()` in mock mode — check `self.mock` first.
- **Tests are hermetic** — `backend/tests/conftest.py` pins mock mode. Keep `python -m pytest -q`
  green before and after changes.
- **Don't reintroduce** the Postgres memory path or a SQLite layer — persistence is the vault.

## Workflow

- Branch per phase (e.g. `phase-1-docs-pivot`). Don't commit/push unless asked — the owner
  squash-merges after review.
- Update `PROJECT_STATE.md` at the end of a session.
