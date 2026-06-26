# FounderOS — Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what phase we just finished, what phase we're on, what's working, what's
> broken, and what to do next. Read this first at the start of any new session.
>
> **PRD / source of truth for phases:** `docs/blueprint.html` (Build Blueprint v1.0) — 10 phases (0–9).

**Last updated:** 2026-06-25
**Current phase:** Phase 3 — LangGraph Orchestration (NOT STARTED — up next)
**Overall completion:** ~58% (Phases 0, 1, 2 done)
**LLM mode:** mock (no API key yet — `USE_MOCK_LLM=true`)
**Tests:** 10/10 passing (`python -m pytest -q` from repo root, inside `.venv`)
**Branch:** `phase-2-agents` (ready to merge into `main`)

---

## Phase Tracker (from the blueprint)

| Phase | Name | Status |
|---|---|---|
| 0 | Scaffold & Tooling | ✅ Done |
| 1 | Provider & Mock Layer | ✅ Done |
| 2 | Agent Abstraction + 7 Agents | ✅ Done (all 7 agents) |
| 3 | LangGraph Orchestration | ⬜ Not started ← NEXT |
| 4 | Debate & Consensus Engine | 🟡 Largely built, not the current focus |
| 5 | Memory Loop (episodic + semantic) | 🟡 Modules written, NOT wired |
| 6 | MCP Integration | ⬜ Not started (placeholder pkg only) |
| 7 | Frontend | 🟡 Components exist, integration unverified |
| 8 | Benchmark Harness | ⬜ Not started (placeholder pkg only) |
| 9 | Go Live (insert keys) | ⬜ Not started |

---

## What we JUST did (Phase 2 — COMPLETE, on branch `phase-2-agents`)

- **Task 1 — Audited all 6 existing agents.** All pass (subclass + `SYSTEM_PROMPT` +
  `_mock_response()` + structured `analyze()`). No fixes needed.
- **Task 2 — Built `agents/founder_fit.py`** (`FounderFitAgent`). Standalone `BaseAgent`,
  `llm_model = DEEP_MODEL`, follows the scout.py pattern (module-level `_MOCK` + `SYSTEM_PROMPT`).
  Scores 5 dimensions (founder_background, domain_expertise, execution_history, team_composition,
  coachability) each with score+rationale, plus `overall_fit_score`, `strengths`, `gaps`, `summary`.
  **`venture_partner.py` left untouched** (its founder-fit fields/prompt still exist — see Notes).
- **Task 3 — Registered** in `agents/__init__.py` and `main.py`. Pipeline is now:
  Scout → Trend/Finance/Growth → Skeptic → **Founder-Fit** → Debate → Venture Partner.
  `founder_fit_output` also passed into `vp_context` (VP doesn't read it yet — VP untouched).
- **Task 4 — Verified mock mode:** all 7 mock fixtures parse as valid JSON; full pipeline
  returns 7 agent outputs including "Founder-Fit Agent". No malformed fixtures.
- **Task 5 — Tests:** added `test_founder_fit_mock_returns_expected_keys` and
  `test_founder_fit_analyze_returns_structured_output`; renamed/upgraded the six-agent test to
  `test_all_seven_agents_appear_in_output` (now asserts exact set of 7). **10/10 passing.**

## What's WORKING

- Full pipeline runs end-to-end in mock mode: `POST /api/analyze` → Scout → Trend/Finance/Growth
  → Skeptic → Debate → Venture Partner → `VentureRecommendation`.
- `QwenProvider` (qwen-turbo / qwen-plus via DashScope), JSON-mode, 3-attempt retry, in-process
  cache, mock fallback (raises in mock mode; agents supply their own `_mock_response`).
- `config.py` `is_live` gating; health check at `GET /` reports mock vs live.
- 8/8 tests pass.

## What's NOT working / known gaps

- Memory modules (`memory/episodic.py`, `memory/semantic.py`) are written but **not wired** into
  `main.py` — recommendations use an in-memory dict; nothing learns yet. (Phase 5 — later.)
- No LangGraph orchestration — `main.py` runs agents **sequentially**, not in parallel. (Phase 3.)
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
- `backend/main.py` — `run_agent_society()` pipeline + FastAPI endpoints
- `backend/models.py` — `UserProfile`, `AgentOutput`, `StartupIdea`, etc.
- `backend/tests/test_pipeline.py` — existing tests

## Next session should start by

1. Reading this file.
2. If Phase 2 is done: update the tracker and begin Phase 3 (LangGraph) or Phase 5 (wire memory).
3. Running `python -m pytest -q` to confirm baseline is green before changing anything.
