# FounderOS — Two-Layer AI Agent Society for Business Decisions

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **QwenCloud Hackathon 2026 — Track 3: Agent Society**
>
> FounderOS runs an **8-agent board debate** to evaluate a business decision, then a **nested
> 3-agent council** to pressure-test the board's own reasoning — and proves the council catches
> what a single agent misses.

**Live demo:** [founderos-zeta.vercel.app](https://founderos-zeta.vercel.app) | **Backend:** [vincent-playground-founderos-api.hf.space](https://vincent-playground-founderos-api.hf.space)

---

## What it does

An operator brings **one business decision** — *"Should we expand into Vietnam next quarter?"* —
and FounderOS assembles two layers of agents that evaluate, debate, and return a **board-ready memo**:

**From:** `"Should we expand into Indonesia next quarter, or deepen at home first?"`  
**To:** `"Conditional — pilot one corridor. Here's the dissent, what's missing, and a phased plan."`

The memo is explicit about its own limits: `missing_inputs[]`, `what_would_change_this_call`,
an attributed `dissent[]` record, and a one-line disclaimer. Advisory — the operator owns the call.

---

## Track 3 — Agent Society

FounderOS implements two coordinated agent layers. See the [full architecture diagram](docs/architecture-diagram.md).

### Layer 1: The Board (8 agents via LangGraph)

```
vault.read (LLM-selected notes)
    │
    ▼
Scout → Market Intelligence → [Trend ∥ Finance ∥ Growth ∥ Capability] → Skeptic → Debate Engine → Chair
                                      (parallel fan-out, asyncio.gather)
    │
    ▼
vault.write_back (decision note + outcome loop)
```

| Agent (`name`) | Role |
|---|---|
| `scout` | Frames the options on the table for this decision |
| `research` (Market Intelligence) | Fetches real-world benchmarks via MCP (web / news / Crunchbase) |
| `trend` | Reads market/demand signals |
| `finance` | Models the decision against company P&L and unit economics |
| `growth` | Maps execution and go-to-market |
| `skeptic` | **The main event** — attacks the weakest assumptions |
| `capability` | Scores organisational readiness to execute |
| `venture_partner` (Chair) | Synthesises the board memo |

The **Debate Engine** detects conflicts between agents, runs ≤3 revision rounds with severity-weighted
consensus scoring, and surfaces unresolved conflicts as the auditable `dissent[]` record.

### Layer 2: Feedback Intelligence Council (Track 3 centrepiece)

A **separate 3-agent mini-council** reads user feedback notes from the vault and produces a ranked
product brief — while demonstrating measurable efficiency gains over single-agent analysis.

```
Feedback Vault Notes
    │
    ▼
Feedback Analyst → Feedback Skeptic → Feedback Chair
(cluster themes)   (challenge bias)    (accept/reframe/override)
    │
    ▼
CouncilBriefResponse: council_dialogue[] + overrides[] + baseline_comparison
```

| Track 3 Criterion | Where it shows |
|---|---|
| Task decomposition + role assignment | 11 agents across 2 layers, each with a distinct system prompt |
| Dialogue and negotiation | `council_dialogue: CouncilTurn[]` — every turn rendered in the UI |
| Conflict resolution | Debate engine `overrides[]`: accepted / reframed / overridden per Skeptic challenge |
| **Measurable efficiency gain** | `baseline_comparison.corrections_count` — integer delta, council vs. single agent |

### Cross-Track Elements

| Track | FounderOS element |
|---|---|
| **Track 1 — MemoryAgent** | Per-company Obsidian markdown vault: LLM-driven selective retrieval + write-back. The board remembers prior decisions across sessions (no RAG / no vector DB). |
| **Track 4 — Autopilot Agent** | `execution_plan` in `BoardRecommendation`: a phased business workflow (Validate → Pilot → Scale) generated automatically from the board debate. |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TailwindCSS (Vercel Hobby) |
| Backend | FastAPI, Python 3.11 (HF Spaces Docker, port 7860) |
| Agent orchestration | LangGraph — parallel analyst fan-out via `asyncio.gather` |
| AI model | **Qwen** (qwen-turbo / qwen-plus via DashScope) — JSON mode, 3-attempt retry |
| Memory | Per-company Obsidian markdown vault — LLM-driven selective retrieval, no embeddings |
| Retrieval | LLM note-selector over frontmatter index (keyword-overlap fallback in mock mode) |
| MCP | Crunchbase / web search / news — mock-safe fallback |
| Auth | Stubbed company picker → vault folder |

---

## Getting started

### Backend

```bash
python -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Set QWEN_API_KEY or leave USE_MOCK_LLM=true for keyless mock mode
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend && npm install
# .env.local: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev   # → http://localhost:3000
```

### Tests (hermetic — no API key needed)

```bash
python -m pytest -q   # 72/72 passing
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | `{ company_id, profile?, decision }` → `BoardResponse` |
| `GET` | `/api/response/{id}` | Fetch saved response |
| `POST` | `/api/feedback` | Write outcome back to vault |
| `GET` | `/api/company/{id}` | Decision history |
| `POST` | `/api/council-brief` | `{ company_id }` → `CouncilBriefResponse` (Track 3) |

Full contract: [`docs/architecture.md`](docs/architecture.md) | Architecture diagram: [`docs/architecture-diagram.md`](docs/architecture-diagram.md)

---

## Deploying

Backend on **Hugging Face Spaces** (Docker, free CPU Basic) — a long-running container holds the
~90–240s debate run that serverless can't. Frontend on **Vercel Hobby**. Full steps: [`docs/deployment.md`](docs/deployment.md).

---

## Project structure

```
founderos/
├── frontend/src/
│   ├── app/boardroom/          # Main decision intake → board memo
│   │   └── council/            # Feedback Intelligence Council UI (Track 3)
│   ├── components/
│   │   ├── CouncilBrief.tsx    # Council dialogue + efficiency gain (Track 3)
│   │   ├── BoardMemo.tsx       # Board memo renderer
│   │   ├── AgentDebate.tsx     # Live debate visualisation
│   │   └── CouncilReasoning.tsx
│   └── lib/types.ts            # TS mirror of backend/models.py
│
├── backend/
│   ├── agents/                 # 8 board agents + 3 feedback council agents
│   ├── consensus/
│   │   ├── debate_engine.py    # Conflict detection + rounds + severity-weighted consensus
│   │   └── feedback_council.py # 3-agent mini-council orchestrator (Track 3)
│   ├── vault/store.py          # Per-company markdown vault (read / write-back / feedback)
│   ├── graph.py                # LangGraph orchestration
│   └── models.py               # Pydantic v2 contract (source of truth)
│
├── vault/                      # Seed vault baked into Docker image
│   ├── harborline-logistics/   # 8 decisions + 3 feedback notes + _profile.md
│   └── lumen-skincare/         # 5 decisions + _profile.md
│
└── docs/
    ├── architecture.md         # Frozen Phase 0 contract
    ├── architecture-diagram.md # Mermaid system diagram
    └── deployment.md
```

---

## License

MIT — see [LICENSE](LICENSE).
