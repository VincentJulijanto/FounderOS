# FounderOS — Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what phase we just finished, what phase we're on, what's working, what's
> broken, and what to do next. Read this first at the start of any new session.
>
> **PRD / source of truth for phases:** `docs/blueprint.html` (Build Blueprint v1.0) — 10 phases (0–9).

**Last updated:** 2026-06-25
**Current phase:** Phase 5 — Memory Loop (NEXT — start only now that Sprints A/B/C are handled).
Phase 4 (Debate) built earlier; Phase 7 (Frontend) now wired to real data.
**Overall completion:** ~74% (Phases 0–3 done; Phase 4 debate functional; Phase 7 frontend wired)
**LLM mode:** mock (no API key yet — `USE_MOCK_LLM=true`)
**Tests:** 12/12 passing (`python -m pytest -q` from repo root, inside `.venv`)
**Branch:** `phase-3-langgraph` (branched off `phase-2-agents`, NOT merged to main — awaiting
partner discussion on the phase-2 branch)

---

## Audit follow-up sprints (2026-06-25) — A ✅ / B ⏸ deferred / C ✅

### Sprint A — pre-flight cleanup ✅ (commit `6f12541`)
- **A1 Tailwind:** added `frontend/postcss.config.js`; added the color shades the UI
  actually uses but were undefined (`brand-400/800/950`, `accent-400`). `npm run build`
  now compiles and the UI is styled (was unstyled — no postcss config + purged classes).
- **A2 Founder-Fit score:** VP no longer emits its own number. `venture_partner.py` reads
  `context["founder_fit_output"]` and overwrites `founder_fit_score` on every idea with the
  dedicated agent's score; also feeds the canonical number into the VP prompt summary.
  Verified: FounderFitAgent **6.6** == StartupCard **6.6** (was 6.6 vs 8.2).
- **A3 Doc drift:** README / architecture.md / demo_script.md → Qwen (not Claude), 7 agents
  (not 6), LangGraph parallel fan-out, real memory stack (PostgreSQL+Qwen, no Chroma/Qdrant).
  Frontend "6 agents" text + icon rosters → 7 everywhere.

### Sprint B — live smoke test ⏸ DEFERRED, NOT RUN (no API key)
- **No `.env` / no `QWEN_API_KEY` available** at audit time (user chose "proceed to C, defer B").
- **Still required before trusting live mode.** Nothing about real-model behaviour is verified:
  whether all 7 agents return parseable JSON, whether `_parse_json` survives real Qwen output,
  whether the debate engine actually fires (`debate_rounds > 0`) on real conflicts. **Run this
  before relying on live mode or demoing with a key.**

### Sprint C — AgentDebate wired to real data ✅ (commit `c779f1f`)
- Removed the hardcoded "AI Study Buddy / NUS" debate fixture and the fake
  `setTimeout('debating', 3000)` timer. AgentDebate now renders the real 7-agent roster
  (live roles + scores), real `debate_rounds` (conflicts / revised positions / moderator
  verdict), and the real `debate_summary`, all from `/api/analyze` props.
- Backend now exposes `debate_summary` on `VentureRecommendation`.
- **Known limitation (ties to Sprint B):** in **mock mode the debate engine returns
  `_MOCK_NO_CONFLICT` → 0 rounds**, so the debate centerpiece only shows the consensus
  message. The round-by-round UI is built and handles real rounds, but needs a **live key**
  to populate. Deliberately did NOT fabricate mock conflicts (that's the fake content the
  audit removed). Consider a representative mock-debate fixture later if demoing keyless.

---

## Phase Tracker (from the blueprint)

| Phase | Name | Status |
|---|---|---|
| 0 | Scaffold & Tooling | ✅ Done |
| 1 | Provider & Mock Layer | ✅ Done |
| 2 | Agent Abstraction + 7 Agents | ✅ Done (all 7 agents) |
| 3 | LangGraph Orchestration | ✅ Done (parallel analyst fan-out) |
| 4 | Debate & Consensus Engine | 🟡 Built & wired as a graph node |
| 5 | Memory Loop (episodic + semantic) | 🟡 Modules written, NOT wired ← NEXT |
| 6 | MCP Integration | ⬜ Not started (placeholder pkg only) |
| 7 | Frontend | 🟡 Wired to real data (AgentDebate live); not browser-smoke-tested with a key |
| 8 | Benchmark Harness | ⬜ Not started (placeholder pkg only) |
| 9 | Go Live (insert keys) | ⬜ Not started |

---

## What we JUST did (Phase 3 — COMPLETE, on branch `phase-3-langgraph`)

- Installed `langgraph==0.1.9` into `.venv` (was in requirements.txt but never installed).
- **Built `backend/graph.py`** — a LangGraph `StateGraph`. Nodes: scout → analysts → skeptic →
  founder_fit → debate → venture_partner. State is a `TypedDict` (`GraphState`) with a dict-merge
  reducer on `agent_outputs` and `operator.add` on `errors`.
- **Parallel fan-out is real:** `analysts_node` runs Trend/Finance/Growth via
  `asyncio.gather(asyncio.to_thread(...))`. Agents are sync, so `to_thread` gives true concurrency.
  Proven: 3×0.5s injected delays complete in 0.52s (would be 1.5s sequential).
- **Wired into `main.py`:** `/api/analyze` is now `async` and `await build_recommendation(profile)`
  → `run_graph()`. Kept a **sync `run_agent_society` wrapper** (`asyncio.run`) so the existing
  tests and any sync callers keep working. Removed now-unused agent/DebateEngine imports from main.
- **Response shape unchanged** — verified over HTTP: 7 agents in order, execution plan, roadmap,
  debate_rounds. Debate engine still runs (as a node), untouched.
- **Tests:** added `test_analyst_fanout_all_three_present` (TestClient → /api/analyze, all 3
  analysts + 7 total) and `test_run_graph_state_has_expected_keys` (async, asserts state keys).
  **12/12 passing.**

### Earlier (Phase 2 — on `phase-2-agents`, merged into this branch's history)
- Built `FounderFitAgent` (7th agent, DEEP_MODEL, 5 dimensions). VP left untouched.
  Registered between Skeptic and VP. Tests went 8 → 10.

## What's WORKING

- Full pipeline runs end-to-end in mock mode: `POST /api/analyze` → Scout → Trend/Finance/Growth
  → Skeptic → Debate → Venture Partner → `VentureRecommendation`.
- `QwenProvider` (qwen-turbo / qwen-plus via DashScope), JSON-mode, 3-attempt retry, in-process
  cache, mock fallback (raises in mock mode; agents supply their own `_mock_response`).
- `config.py` `is_live` gating; health check at `GET /` reports mock vs live.
- 8/8 tests pass.

## What's NOT working / known gaps

- Memory modules (`memory/episodic.py`, `memory/semantic.py`) are written but **not wired** into
  the graph — recommendations use an in-memory dict; nothing learns yet. `run_graph` already
  threads a `memory_context` param end-to-end, so Phase 5 is mostly integration. (NEXT.)
  - **REQUIRED Phase 5 fix (do not defer):** even though `memory_context` is threaded into the
    graph and into `vp_context["memory_context"]`, the **VP prompt never uses it** — once memory
    is wired, the VP must actually fold `memory_context` into its user message / synthesis, or
    learning won't influence recommendations. This is part of Phase 5, not a later cleanup.
- `mcp/` and `benchmark/` are placeholder packages only. (Phases 6, 8.)
- **Sprint B not run** — real-model JSON parsing / debate-firing unverified (see audit section).
- ~~Doc drift~~ ✅ fixed in Sprint A (Claude→Qwen, 6→7 agents, LangGraph fan-out, real memory stack).

## Phase 2 notes / deviations

- ~~**Founder-fit now lives in two places.**~~ ✅ RESOLVED in Sprint A2. `FounderFitAgent` is the
  single source of truth: `VenturePartnerAgent.analyze` now reads `context["founder_fit_output"]`
  and overwrites `founder_fit_score` on every idea with that agent's score (and surfaces the
  canonical number in the VP prompt summary). VP's qualitative founder-fit prompt fragment +
  `founder_fit_rationale` remain as guidance text only. UI now shows one consistent number (6.6).
- Pipeline step comments in `main.py` were renumbered (Founder-Fit inserted as Step 4; Debate→5, VP→6).

## Architectural decisions / conventions to remember

- Each agent owns its own `SYSTEM_PROMPT` (module constant) and a `_MOCK` JSON string returned by
  `_mock_response()`. `analyze(profile, context)` calls `self._call_llm(...)` → `self._parse_json(...)`
  → returns an `AgentOutput`.
- Model tiering: reasoning-heavy agents set `llm_model = DEEP_MODEL` (Skeptic, VP); others default
  to `FAST_MODEL`. Founder-Fit should use `DEEP_MODEL` (judgment-heavy).
- Mock mode must keep working throughout — no live key required.
- Do NOT touch the debate engine, memory modules, or LangGraph during Phase 2.

## Key Files

- `backend/agents/base.py` — `BaseAgent` (`_call_llm`, `_mock_response`, `_parse_json`, `_format_profile`)
- `backend/agents/scout.py` — cleanest reference for a FAST agent
- `backend/agents/venture_partner.py` — DEEP agent; contains the founder-fit prompt fragment to promote
- `backend/agents/__init__.py` — agent registry/exports
- `backend/graph.py` — **LangGraph orchestrator** (`GraphState`, nodes, `run_graph()`); parallel analysts
- `backend/main.py` — `build_recommendation()` (async) + `run_agent_society()` sync wrapper + endpoints
- `backend/models.py` — `UserProfile`, `AgentOutput`, `StartupIdea`, etc.
- `backend/tests/test_pipeline.py` — existing tests

## Next session should start by

1. Reading this file.
2. Running `python -m pytest -q` to confirm baseline is green (12/12) before changing anything.
3. **Begin Phase 5 (Memory Loop)** — Sprints A & C are done; B is deferred (no key). When wiring
   memory, the **VP-uses-`memory_context` fix is mandatory inside Phase 5** (see gaps above).
4. **Run Sprint B** (live smoke test) whenever a `QWEN_API_KEY` becomes available — it is still
   outstanding and blocks any confidence in live-mode JSON parsing + debate firing.
