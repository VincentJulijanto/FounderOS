# Research Agent — Design Spec

**Status:** Design spec — not yet implemented  
**Canonical name:** `research`  
**Display label:** Market Intelligence

---

## 1. Purpose and Motivation

The board currently reasons only from what the operator provides. A founder submits a question about opening a warehouse in Vietnam, switching to a local 3PL, or entering a new vertical — and the seven agents work with no real-world numbers. Land prices. Logistics rates. Market sizes. Regulatory costs. Analysts compensate with caveats ("we'd need to verify…"), but the memo ends up weaker than it should be.

The Research agent closes that gap. It runs after Scout frames the options, hits the web to pull real-world numbers, and packages those numbers as a structured brief that the four analysts (Trend, Finance, Growth, Capability) all read before writing their outputs. The memo stops asking "what would we need to know?" and instead carries actual data into the recommendation.

The Research agent's job is **data fetching and structured citation** — not analysis. It pulls the numbers, packages them with source URLs and confidence levels, and hands them forward. Analysis belongs to the downstream agents.

---

## 2. Identity

| Property | Value |
|---|---|
| Canonical name string | `research` |
| Display label | `Market Intelligence` |
| Module | `backend/agents/research.py` |
| Class | `MarketResearchAgent` |
| `llm_model` | `FAST_MODEL` (`qwen-turbo`) |
| `max_tokens` | `3000` |
| `score` | `None` — does not score the decision |

The canonical name follows the existing pattern: one lowercase word, used as the dict key in `agent_outputs`, as the `agent_name` field in `AgentOutput`, and as the graph node key.

Full canonical name list becomes:
```
scout · trend · finance · growth · skeptic · capability · venture_partner · research
```

`FAST_MODEL` is correct here. The agent runs one LLM call to generate search queries (cheap), fans out MCP calls (network I/O), then one structured-output call to normalise the results. It does not do deep reasoning — that is the analysts' job.

---

## 3. Graph Position and Data Flow

### Current graph

```
scout_node → analysts_node (trend ∥ finance ∥ growth ∥ capability) → skeptic_node → debate_node → venture_partner_node
```

### With Research

```
scout_node → research_node → analysts_node (trend ∥ finance ∥ growth ∥ capability) → skeptic_node → debate_node → venture_partner_node
```

Research sits between Scout and the analyst fan-out. Scout frames the options; Research fetches real-world data for those options; the analysts each receive a `research_brief` context block alongside the standard decision context.

### What Research reads from GraphState

- `state["decision"]` — the full `Decision` object (question, context, constraints, options)
- `state["options"]` — the options Scout framed
- `state["company_profile"]` — the `CompanyProfile`
- `state["vault_context"]` — vault history block

### What Research writes to GraphState

- `agent_outputs["research"]` — the standard `AgentOutput` (citations in `raw_data`)
- `research_brief` — a formatted string injected into every downstream agent's context

`GraphState` needs one new key: `research_brief: str`.

### How analysts receive the brief

Each analyst's `analyze()` call receives a `context` dict. The `analysts_node` includes `research_brief` in that dict:

```python
ctx = {
    **_base_context(state),
    "research_brief": state.get("research_brief", ""),
}
```

Each analyst renders the brief in its user message via a shared helper on `BaseAgent`:

```python
def _format_research_brief(self, context: dict) -> str:
    brief = context.get("research_brief", "")
    return f"\n## Market Intelligence Brief\n{brief}\n" if brief else ""
```

If `research_brief` is absent or empty the block is omitted — the agent behaves exactly as today.

---

## 4. Research Query Generation

One `FAST_MODEL` call produces 3–5 targeted search queries from the decision question + framed options. The prompt instructs the model to be specific: include country or market names, unit types (price per sqm, rate per km, USD or SGD), and a date signal (2025 or 2026).

Prompt inputs:
- Decision question and context
- Company sector and stage
- Framed options (from Scout)
- Constraints (budget, timeline)

Expected output:

```json
{
  "queries": [
    "warehouse lease price per sqm Ho Chi Minh City 2025",
    "Vietnam 3PL last-mile delivery rates 2025",
    "Vietnam logistics market size CAGR 2025",
    "customs clearance cost importer Vietnam B2B",
    "competitor last-mile delivery pricing Southeast Asia"
  ]
}
```

The agent accepts 3–5 queries. Fewer than 3 gets padded with a generic sector benchmark query; more than 5 clips to the first 5. The existing Qwen JSON-mode retry in `QwenProvider` handles parse failures.

---

## 5. MCP Tools Used

After query generation, MCP calls fan out in parallel via `asyncio.gather`:

| Tool | Calls |
|---|---|
| `mcp_client.search_web(query)` | Once per generated query (3–5 calls) |
| `mcp_client.fetch_news(topic)` | Once — sector + decision question as topic |
| `mcp_client.search_crunchbase(sector)` | Once — market sizing context |

`fetch_financials` is **not** used by Research — that is the Finance agent's domain.

Because `research_node` is `async def`, MCP calls run natively async without `run_sync`. The agent's public `analyze()` method remains synchronous (matching `BaseAgent`) and uses `run_sync` to call the async internals — the same pattern Scout and Finance use, extended to fan out multiple calls.

---

## 6. Output Schema

### AgentOutput fields

| Field | Content |
|---|---|
| `agent_name` | `"research"` |
| `role` | `"Market Intelligence — real-world data brief for the board"` |
| `analysis` | One-paragraph summary: headline numbers found + biggest data gap |
| `score` | `None` |
| `key_findings` | Headline numbers as plain strings: `"Vietnam 3PL rates: USD 2.50–4.00/kg (Statista 2025)"` |
| `concerns` | Data gaps: searches that returned no usable numbers |
| `recommendations` | Empty list |
| `raw_data` | Structured citation objects (see below) |

### raw_data shape

```json
{
  "data_points": [
    {
      "metric": "warehouse lease rate",
      "value": "USD 12–18 per sqm/month",
      "geography": "Ho Chi Minh City, Vietnam",
      "source_url": "https://...",
      "source_label": "CBRE Vietnam Industrial Market Q3 2025",
      "date_retrieved": "2026-07-09",
      "confidence": "high"
    }
  ],
  "queries_used": ["query 1", "query 2"],
  "mcp_sources": ["[MOCK] web: warehouse lease price per sqm Ho Chi Minh City 2025"],
  "data_gaps": ["No usable data for customs clearance cost per shipment in Vietnam"]
}
```

**Confidence levels:**
- `"high"` — specific numeric figure from a named source with a date
- `"medium"` — a range, or a number from a source without a clear date
- `"low"` — proxy figure, inferred from adjacent data, or from a mock/thin source

### research_brief string (what analysts read)

```
## Market Intelligence Brief

Data retrieved: 2026-07-09

**Headline numbers:**
- Warehouse lease rate (Ho Chi Minh City): USD 12–18/sqm/month — CBRE Vietnam Q3 2025 [high confidence]
- Last-mile delivery rate (Vietnam 3PL): USD 2.50–4.00/kg — Statista 2025 [medium confidence]
- Vietnam logistics market size: USD 40B, 14% CAGR — ResearchAndMarkets 2025 [medium confidence]

**Data gaps:**
- No usable data found for customs clearance cost per shipment in Vietnam

Sources: https://..., https://...
```

---

## 7. BoardResponse Change

One new field on `BoardResponse` in `backend/models.py`:

```python
research_sources: List[str] = []
```

A deduplicated list of the real-world URLs returned by Research, with the `[MOCK] ` prefix stripped. Empty in mock mode. Populated in `build_response()` in `backend/main.py`:

```python
research_out = state["agent_outputs"].get("research")
research_sources: list[str] = []
if research_out:
    research_sources = [
        s for s in research_out.raw_data.get("mcp_sources", [])
        if not s.startswith("[MOCK] ")
    ]
```

`mcp_used` and `mcp_sources` on `BoardResponse` are unchanged — they already collect provenance from all agents.

---

## 8. Mock Mode

In mock mode, `_mock_response()` returns a hardcoded JSON fixture. Both LLM calls and all MCP calls are bypassed — the agent short-circuits at `self.mock` before any network I/O. The MCP client's own mock fallback is a secondary safety net.

Mock fixture uses `https://mock.research.example.com/...` URLs (identifiably fake, no `[MOCK] ` prefix in the URL string itself — the prefix goes in `mcp_sources`):

```json
{
  "data_points": [
    {
      "metric": "warehouse lease rate",
      "value": "USD 12–18 per sqm/month",
      "geography": "Ho Chi Minh City, Vietnam",
      "source_url": "https://mock.research.example.com/cbre-vietnam-industrial-2025",
      "source_label": "CBRE Vietnam Industrial Market Q3 2025 [MOCK]",
      "date_retrieved": "2026-07-09",
      "confidence": "medium"
    },
    {
      "metric": "last-mile delivery rate (3PL partnership)",
      "value": "USD 2.50–4.00 per kg",
      "geography": "Vietnam (national)",
      "source_url": "https://mock.research.example.com/statista-vietnam-logistics-2025",
      "source_label": "Statista Vietnam Logistics Report 2025 [MOCK]",
      "date_retrieved": "2026-07-09",
      "confidence": "medium"
    },
    {
      "metric": "logistics market size",
      "value": "USD 40B, 14% CAGR",
      "geography": "Vietnam",
      "source_url": "https://mock.research.example.com/researchandmarkets-vn-logistics",
      "source_label": "ResearchAndMarkets Vietnam Logistics 2025 [MOCK]",
      "date_retrieved": "2026-07-09",
      "confidence": "low"
    },
    {
      "metric": "competitor last-mile pricing benchmark",
      "value": "SGD 0.80–1.20 per delivery (SEA average)",
      "geography": "Southeast Asia",
      "source_url": "https://mock.research.example.com/sea-logistics-benchmark-2025",
      "source_label": "SEA Logistics Benchmark Report 2025 [MOCK]",
      "date_retrieved": "2026-07-09",
      "confidence": "low"
    }
  ],
  "queries_used": [
    "warehouse lease price per sqm Ho Chi Minh City 2025",
    "Vietnam 3PL last-mile delivery rates 2025",
    "Vietnam logistics market size growth CAGR",
    "competitor last-mile delivery pricing Southeast Asia"
  ],
  "mcp_sources": [
    "[MOCK] web: warehouse lease price per sqm Ho Chi Minh City 2025",
    "[MOCK] web: Vietnam 3PL last-mile delivery rates 2025",
    "[MOCK] news: Vietnam logistics market",
    "[MOCK] crunchbase: logistics"
  ],
  "data_gaps": [
    "No usable data on customs clearance cost per shipment in Vietnam — queries returned generic regulatory pages only"
  ]
}
```

In mock mode `research_sources` on `BoardResponse` will be `[]` (all mock sources carry the `[MOCK] ` prefix, which the collection loop strips). The UI and PDF renderer must handle an empty list gracefully.

---

## 9. Chair Integration

The Venture Partner (`venture_partner.py`) already reads all `agent_outputs`. The Research agent's `AgentOutput` is included under the key `"research"`. The `_compile_agent_summary` method must be updated to include it in the `labels` dict:

```python
"research": "RESEARCH (market data brief)",
```

The Chair reads Research's `analysis` field (the one-paragraph summary) as part of the board summary before writing the memo. This ensures real-world numbers flow through to the rationale and risk sections.

---

## 10. Sequence Diagram

```
POST /api/analyze
        ↓
   scout_node          (frames options; MCP: crunchbase + news)
        ↓
   research_node       (generates 3–5 queries; MCP: web × N + news + crunchbase;
                        returns data_points + research_brief string)
        ↓
   analysts_node ────────────────────────────────────────────
   trend.analyze(ctx + research_brief)                       |
   finance.analyze(ctx + research_brief)   [parallel]        |
   growth.analyze(ctx + research_brief)                      |
   capability.analyze(ctx + research_brief) ─────────────────┘
        ↓
   skeptic_node        (analyst_summary + research_brief)
        ↓
   debate_node
        ↓
   venture_partner_node  (reads all agent_outputs including "research")
        ↓
   BoardResponse (includes research_sources field)
```

---

## 11. Out of Scope

- Research does not write to the vault — it is transient per-run.
- Research does not call `fetch_financials` — Finance owns that.
- Research does not participate in the debate.
- Caching of research results across runs is not addressed here.
- Frontend changes for displaying `research_sources` as clickable links are a separate task.

---

## 12. Implementation Checklist

Files to create or modify, in dependency order:

| # | File | Change |
|---|---|---|
| 1 | `backend/models.py` | Add `research_brief: str` to `GraphState`; add `research_sources: List[str] = []` to `BoardResponse` |
| 2 | `backend/agents/research.py` | New file — `MarketResearchAgent` class |
| 3 | `backend/agents/__init__.py` | Export `MarketResearchAgent` |
| 4 | `backend/graph.py` | Add `research_node`, `_render_research_brief()` helper, edges `scout→research→analysts`; inject `research_brief` into analyst + skeptic context dicts |
| 5 | `backend/agents/venture_partner.py` | Add `"research"` to `_compile_agent_summary` labels dict |
| 6 | `backend/agents/base.py` | Add `_format_research_brief(context)` helper |
| 7 | `backend/agents/trend.py`, `finance.py`, `growth.py`, `capability.py` | Call `_format_research_brief(context)` in user message construction |
| 8 | `backend/main.py` | Populate `research_sources` in `build_response()` |

### Verification

- `python -m pytest -q` passes (mock mode, no API key)
- Mock run: `BoardResponse` has `"research"` in `agent_outputs`, `research_sources == []`, `research_brief` non-empty in GraphState
- Live run: `research_sources` contains real URLs; analyst outputs reference specific numbers from the brief
