# FounderOS — Project State

> **Living document.** Claude updates this at the end of every chat session. It is the single
> source of truth for: what phase we just finished, what phase we're on, what's working, what's
> broken, and what to do next. Read this first at the start of any new session.
>
> **PRD / source of truth for phases:** `docs/blueprint.html` (Build Blueprint v1.0) — 10 phases (0–9).

**Last updated:** 2026-06-28
**Current phase:** Phase 6 — MCP Integration ✅ DONE. Sprint B (live smoke test) RAN 2026-06-28 →
🟠 **PARTIAL/BLOCKED: live mode is broken** (Skeptic truncates at `max_tokens=2000`; `/api/analyze`
500s). Phase 7 (Frontend) + Phase 8 (Benchmark) remain; Phase 9 (Go Live) blocked on the Skeptic fix.
Phase 5 (Memory), Phase 4 (Debate), Phase 3 (LangGraph) done earlier.
**Overall completion:** ~88% (Phases 0–6 done; Phase 7 frontend wired; 8/9 remaining)
**LLM mode:** mock for the test suite (forced via `backend/tests/conftest.py`). A real `QWEN_API_KEY`
exists in `.env` with `USE_MOCK_LLM=false`, so the **app boots in LIVE mode** and DashScope IS now
reachable (direct call ~1s) — BUT the full pipeline 500s in live mode (see Sprint B). The test suite
is hermetic (conftest pins mock) so `python -m pytest` works regardless. To demo keyless, set
`USE_MOCK_LLM=true` in `.env`.
**Tests:** 44/44 passing (`python -m pytest -q` from repo root, inside `.venv`) — +8 Phase 6 MCP tests
**Branch:** `phase-6-mcp` (branched off `phase-5-memory-loop`). Not yet merged — open a PR when
partner-reviewed. Do NOT merge to main.

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

### Sprint B — live smoke test 🟠 RUN 2026-06-28 — **PARTIAL / BLOCKED** (live mode broken)
- **Now ran with a real key** (`QWEN_API_KEY` present, `USE_MOCK_LLM=false`, DashScope reachable —
  direct provider call returned valid JSON in ~1s). Ran `uvicorn backend.main:app` (live, no mock
  warnings) and `POST /api/analyze`. **Result: HTTP 500 — live mode does NOT work end-to-end.**
- **ROOT CAUSE — Skeptic agent truncates at the token ceiling.** `BaseAgent` calls the LLM with
  `max_tokens=2000` for every agent. In live mode the Skeptic's full per-opportunity JSON over 5
  opportunities exceeds that. Confirmed directly: `finish_reason='length'`, `completion_tokens=2000`,
  `char_len≈9056`, JSON unparseable (`Unterminated string ... char 9045`). The 3-attempt retry
  cannot help — every attempt hits the same ceiling. Mock mode never exposed this (short complete
  fixtures). API error: `Agent pipeline failed: Qwen returned invalid JSON after 3 attempts on
  model qwen-plus. Last error: Unterminated string starting at: line 96 column 19 (char 8953)`.
- **Per-agent live verification (isolated):** Scout ✅, Trend ✅, Finance ✅, Growth ✅, Founder-Fit ✅
  all called the real LLM and returned **valid parseable JSON** (8–14s each). **Skeptic ❌** (fails
  after 110s / 3 retries). **Venture Partner — never reached** (pipeline aborts at Skeptic).
- **The 7 checks (PASS/FAIL/BLOCKED):**
  1. HTTP 200 — **FAIL** (HTTP 500).
  2. All 7 agents present — **FAIL** (6/7 proven to work in live mode; Skeptic crashes; VP unreached).
  3. No `[MOCK]` in agent output — **PARTIAL**: the 6 agents that ran used real LLM output.
     ⚠️ Caveat: by Phase-6 design `mcp_sources` always carries `"[MOCK] …"` labels until real MCP
     creds exist, so a literal `[MOCK]` substring search on the response is NOT a valid mock detector.
  4. `debate_rounds > 0` — **BLOCKED / STILL UNVERIFIED** (debate runs after Skeptic; never reached).
     Unverified since Phase 3.
  5. founder_fit alignment — **BLOCKED** (the alignment fix lives in the VP, which never runs;
     the Founder-Fit *agent* itself did produce a score in live mode).
  6. `mcp_used` true — **BLOCKED + SEMANTIC MISMATCH**: no response to inspect, AND the Phase-6
     implementation sets `mcp_used=True` only for *live* MCP data; with mock MCP fixtures it is
     `False` (verified False in the keyless run). The check's "should always be true" expectation
     contradicts the implemented semantics.
  7. `=== Founder Memory ===` block — **BLOCKED** (injected in the VP prompt; VP never runs).
- **Step 4 (second run / memory influence)** — **BLOCKED**: first run 500s, so no baseline to diff.
- **Process note:** the Sprint B payload (`startup_name`/`industry`/`description`/`founder_background`)
  does NOT match the real `/api/analyze` contract (`{"profile": UserProfile}` with name/background/
  skills/budget/weekly_hours/interests/goals). It was translated faithfully to a `UserProfile` to run.
- **FIX (deferred — not applied this sprint):** raise `max_tokens` for deep/large-output agents
  (Skeptic, and likely VP next) to ~4000–8000, and/or cap per-opportunity verbosity / opportunity
  count. Then re-run Sprint B and re-check items 1–7 + Step 4. No code changed in this commit.

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
| 5 | Memory Loop (episodic + semantic) | ✅ Done — wired end-to-end, in-process store, VP consumes it |
| 6 | MCP Integration | ✅ Done — MCPClient (mock+live), Scout+Trend wired, mcp_used/sources in API |
| 7 | Frontend | 🟡 Wired to real data (AgentDebate live); not browser-smoke-tested with a key |
| 8 | Benchmark Harness | ⬜ Not started (placeholder pkg only) ← NEXT |
| 9 | Go Live (insert keys) | ⬜ Not started |

---

## What we JUST did (Phase 6 — COMPLETE, on branch `phase-6-mcp`)

- **Built `backend/mcp/client.py`** — a real async `MCPClient` (singleton `mcp_client`) with
  three methods: `search_crunchbase(query)`, `search_web(query)`, `fetch_news(topic)`.
  - **Mock mode** (default — no `QWEN_API_KEY` OR no `mcp_server_url`): returns deterministic,
    realistically-shaped, non-empty fixtures, query-seeded. Sources are prefixed `"[MOCK] "`.
  - **Live mode** (`is_live` AND `mcp_server_url` set): async `httpx` POST to the MCP server,
    wrapped in try/except — on ANY failure it logs a warning and returns the mock fallback.
    **Never crashes the pipeline.** `httpx` is imported lazily so mock mode needs no HTTP stack.
  - Ships a `run_sync(coro)` bridge so the synchronous agents can call the async methods whether
    or not they sit under a running event loop (LangGraph runs sync nodes both ways).
- **Wired Scout** (`agents/scout.py`): before the LLM call it runs `search_crunchbase(industry)`
  + `fetch_news(industry)` (industry = founder's first interest), injects them under a
  `## Live Market Data` header, and adds `mcp_sources` to its output `raw_data`.
- **Wired Trend** (`agents/trend.py`): runs `search_web("{industry} trends 2026")`, injects under
  a `## Current Signals` header, adds `mcp_sources` to `raw_data`.
- **API surface** (`models.py` + `main.py`): `VentureRecommendation` gained `mcp_used: bool` and
  `mcp_sources: list[str]`. `build_recommendation` gathers every agent's `mcp_sources`, dedupes
  (order-preserving), and sets `mcp_used = any source not `[MOCK]`-prefixed`. Keyless → `mcp_used=False`.
- **Tests:** added `backend/tests/test_mcp.py` (8) — client mock schema for all 3 methods,
  determinism, Scout/Trend `mcp_sources`, `/api/analyze` exposes `mcp_used`+`mcp_sources`.
  Added `backend/tests/conftest.py` to force mock mode session-wide (see flag below). **44/44 passing.**

- **⚠️ MCP live credentials NOT verified — same deferred pattern as Sprint B.** No `mcp_server_url`
  is configured and the sandbox has no network, so only the mock path has run. The live HTTP path
  (`_post`, auth header, response normalization, fallback-on-error) is written but unexercised.
  **Will be confirmed when `QWEN_API_KEY` and MCP tokens/URL are available** and the host has
  network egress — run alongside Sprint B.
- **⚠️ Env drift discovered this session:** `.env` now contains a real `QWEN_API_KEY` with
  `USE_MOCK_LLM=false`, so the app boots LIVE — but DashScope is unreachable from here, so the
  previously-documented `python -m pytest` (33/33) would HANG on the first live LLM call. Fixed by
  making the suite hermetic via `conftest.py` (pins `use_mock_llm=True` + `mcp_client.live=False`).
  Did NOT modify `.env` (user's deliberate config). To run the app keyless: `USE_MOCK_LLM=true`.

## What we did earlier (Phase 5 — COMPLETE, on branch `phase-5-memory-loop`)

- **Built `backend/memory/store.py`** — an in-process `MemoryStore` (singleton `memory_store`)
  that backs the memory loop with **no Postgres / no API key** required. Holds episodic
  `Episode`s + semantic `Insight`s per `user_id`, thread-safe. This is the active hackathon
  backing; the Postgres `EpisodicMemory`/`SemanticMemory` modules remain as the production schema.
- **`backend/memory/__init__.py` now lazy-imports the Postgres services** via `__getattr__`
  (sqlalchemy/asyncpg are NOT installed) so `memory_store` is always importable keyless.
- **Wired the full loop into `main.py`:**
  - `/api/analyze` → `memory_store.build_context(user_id)` → passed to `build_recommendation`
    → graph → VP. After the run it records an episodic entry (`record_session`).
  - `/api/feedback` → `memory_store.update_outcome(...)` records the real outcome AND re-derives
    semantic insights; the response now returns the refreshed `insights` block.
  - `/api/memory/{user_id}` → returns real episodic history + learned semantic insights.
- **MANDATORY VP fix DONE:** `venture_partner.py` now folds `memory_context` into its user
  message (a `=== Founder Memory ===` block) and the SYSTEM_PROMPT instructs the VP to treat it
  as decisive (don't re-recommend abandoned ideas, respect learned constraints). Empty history →
  "treat as a first session." Verified by a test that captures the prompt.
- **Semantic extraction is heuristic/rule-based** (deterministic, keyless) so learning actually
  happens in mock mode: ≥2 abandonments → constraint, ≥2 launches → track-record pattern,
  score baseline, recurring idea-name theme. Swap for the Qwen `SemanticMemory.extract_and_store`
  when a key is available — same `[LABEL] value` output shape, no caller change.
- **Tests:** added `backend/tests/test_memory.py` (16 tests) — store unit tests, insight
  extraction, VP-prompt-uses-memory, two-user isolation, and HTTP end-to-end
  (analyze→feedback→memory grows). **33/33 passing**, isolation/ordering verified.

## What we did earlier (Phase 3 — COMPLETE, on branch `phase-3-langgraph`)

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

- ~~Memory modules not wired~~ ✅ RESOLVED in Phase 5. Memory loop runs end-to-end via the
  in-process `memory_store`; the VP now consumes `memory_context`. **Known limitation:** the
  active store is **in-process (per-process, resets on restart)** — durable Postgres
  (`EpisodicMemory`/`SemanticMemory`) is written but needs sqlalchemy+asyncpg installed and a
  running DB to activate. Semantic extraction is heuristic in mock mode; the Qwen extractor needs
  a key (ties to Sprint B). Frontend does not yet surface memory (no feedback UI / memory panel).
- ~~`mcp/` placeholder~~ ✅ RESOLVED in Phase 6 — real `MCPClient`, Scout/Trend wired, API surfaces
  `mcp_used`/`mcp_sources`. Live HTTP path unexercised (no `mcp_server_url`/network — see flags above).
- `benchmark/` is a placeholder package only. (Phase 8.)
- **🔴 LIVE MODE BROKEN (Sprint B, 2026-06-28):** `/api/analyze` 500s in live mode — the **Skeptic
  agent** truncates its JSON at `max_tokens=2000` (`finish_reason='length'`). 6/7 agents work live;
  Skeptic crashes; VP/debate never run. `debate_rounds>0` and the VP memory block remain UNVERIFIED.
  Fix (deferred): raise `max_tokens` for deep agents. See Sprint B section for the full check-by-check report.
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
- `backend/memory/store.py` — **in-process Memory Loop** (`MemoryStore`, `memory_store` singleton)
- `backend/memory/episodic.py` / `semantic.py` — Postgres production schema (lazy-imported; not active)
- `backend/mcp/client.py` — **MCP client** (`MCPClient`, `mcp_client` singleton, `run_sync` bridge); mock+live
- `backend/main.py` — `build_recommendation()` (async) + `run_agent_society()` sync wrapper + endpoints
  (load/save memory around `/api/analyze`, learn on `/api/feedback`, collect `mcp_used`/`mcp_sources`)
- `backend/tests/conftest.py` — **forces mock mode session-wide** (hermetic suite, keyless/offline)
- `backend/tests/test_memory.py` — Phase 5 memory-loop tests (16)
- `backend/tests/test_mcp.py` — Phase 6 MCP tests (8)
- `backend/models.py` — `UserProfile`, `AgentOutput`, `StartupIdea`, `VentureRecommendation` (`mcp_used`/`mcp_sources`)
- `backend/tests/test_pipeline.py` — existing tests

## Next session should start by

1. Reading this file.
2. Running `python -m pytest -q` to confirm baseline is green (44/44) before changing anything.
3. **Begin Phase 8 (Benchmark Harness)** — `backend/benchmark/` is a placeholder package only.
   (Phase 7 frontend is wired; consider surfacing `mcp_used`/`mcp_sources` + memory in the UI.)
4. **Run Sprint B + MCP live verification together** now that a `QWEN_API_KEY` is present — but
   ONLY on a host with network egress to DashScope (this sandbox has none). Confirms live-mode
   JSON parsing, debate firing, the Qwen semantic extractor, AND the MCP live HTTP path
   (needs `mcp_server_url` + MCP tokens — currently unset, so MCP runs mock).
5. Decide on `.env`: it currently boots LIVE (`USE_MOCK_LLM=false` + key) but live calls hang
   here. Set `USE_MOCK_LLM=true` to demo keyless, or keep live for a networked host.
6. Optional follow-ups: surface memory in the frontend (feedback UI + memory panel); activate
   durable Postgres memory (install sqlalchemy+asyncpg, run a DB, swap `memory_store`).
