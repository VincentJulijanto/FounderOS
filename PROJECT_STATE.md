# FounderOS — Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what phase we just finished, what phase we're on, what's working, what's
> broken, and what to do next. Read this first at the start of any new session.
>
> **PRD / source of truth for phases:** `docs/blueprint.html` (Build Blueprint v1.0) — 10 phases (0–9).

**Last updated:** 2026-06-25
**Current phase:** Phase 5 — Memory Loop (NEXT). Phase 4 (Debate) already built earlier.
**Overall completion:** ~68% (Phases 0, 1, 2, 3 done; Phase 4 debate engine functional)
**LLM mode:** mock (no API key yet — `USE_MOCK_LLM=true`)
**Tests:** 12/12 passing (`python -m pytest -q` from repo root, inside `.venv`)
**Branch:** `phase-3-langgraph` (branched off `phase-2-agents`, NOT merged to main — awaiting
partner discussion on the phase-2 branch)

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
| 7 | Frontend | 🟡 Components exist, integration unverified |
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
- `mcp/` and `benchmark/` are placeholder packages only. (Phases 6, 8.)
- Doc drift: `README.md` and `docs/architecture.md` say "Claude/Anthropic"; actual stack is Qwen.

## Phase 2 notes / deviations

- **Founder-fit now lives in two places.** Per instruction, `venture_partner.py` was left
  untouched — it still has its own `founder_fit_score` field + prompt fragment + `founder_fit_rationale`.
  The new `FounderFitAgent` is the dedicated source of truth. Later (Phase 3/6 cleanup), the VP
  should consume `founder_fit_output` from context instead of re-deriving its own — right now
  `vp_context["founder_fit_output"]` is passed but ignored by `VenturePartnerAgent._compile_agent_summary`.
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
2. If Phase 2 is done: update the tracker and begin Phase 3 (LangGraph) or Phase 5 (wire memory).
3. Running `python -m pytest -q` to confirm baseline is green before changing anything.
