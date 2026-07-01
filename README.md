# FounderOS — an AI board for business decisions

> An AI board/council that helps operators of **existing businesses** pressure-test a specific
> decision. You bring one call — *"is this sound, and what are we missing?"* — and a **society of
> seven specialized agents** debates it and hands back a **board-ready memo**.

> **⚠ Pivot in progress.** FounderOS is moving from its original "founder profile → startup idea"
> generator to the board/council evaluator described here. The **canonical, frozen Phase 0 contract**
> is in [`docs/architecture.md`](docs/architecture.md); current status and the build plan are in
> [`PROJECT_STATE.md`](PROJECT_STATE.md); the standing brief for contributors is [`CLAUDE.md`](CLAUDE.md).
> Some code still reflects the old framing while the pivot lands.

---

## What it does

FounderOS takes your **company context** and **one decision**, then runs a multi-agent society that
**frames the options**, **reads the market**, **models the economics**, **stress-tests the plan**,
and **debates to a verdict** — then writes a board memo with the reasoning and the dissent.

**From:** `"Should we expand into Indonesia next quarter, or deepen at home first?"`
**To:** `"Conditional — pilot one corridor first. Here's the dissent, what's missing, and a phased plan."`

The memo is explicit about its own limits: a `missing_inputs` list, a `what_would_change_this_call`
section, an attributed `dissent` record, and a one-line disclaimer. It is advisory — the operator
owns the call.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS |
| Backend | FastAPI (Python) |
| Agent orchestration | LangGraph (parallel analyst fan-out) |
| AI model | Qwen (qwen-turbo / qwen-plus via DashScope API) |
| Memory | Per-company **Obsidian markdown vault** (selective retrieval + write-back) |
| Retrieval | LLM-driven note selection over a small vault index — **no embeddings / vector DB** |
| Auth | Stubbed company picker → vault folder (real auth deferred) |

---

## Project structure

```
founderos/
├── frontend/               # Next.js + Tailwind UI
│   └── src/
│       ├── app/            # Landing page + /studio app
│       └── components/     # studio UI, agentRoster, landing/*
│
├── backend/
│   ├── agents/             # 7 specialized agents (being reframed for the pivot)
│   │   ├── scout.py        # frames the options on the table
│   │   ├── trend.py        # market / demand signals for the decision
│   │   ├── finance.py      # models the decision vs company economics
│   │   ├── growth.py       # how the company executes
│   │   ├── skeptic.py      # THE main event — attacks the plan
│   │   ├── founder_fit.py  # → being rebuilt as the Capability agent (org readiness)
│   │   └── venture_partner.py  # the Chair — writes the board memo
│   │
│   ├── consensus/
│   │   └── debate_engine.py    # conflict detection + debate rounds + consensus (reused as-is)
│   │
│   ├── mcp/client.py       # live market data (Crunchbase / web / news), mock + live
│   ├── memory/             # NOTE: episodic.py/semantic.py (Postgres) are UNWIRED and off the
│   │                       #       pivot path. Persistence is the vault (see architecture.md).
│   ├── models.py           # Pydantic data models (rewritten to the frozen contract)
│   ├── config.py           # settings / env vars
│   ├── graph.py            # LangGraph orchestration
│   └── main.py             # FastAPI entry point
│
├── docs/
│   ├── architecture.md     # ← the canonical, frozen Phase 0 contract
│   └── demo_script.md
├── CLAUDE.md               # standing brief for contributors (lanes, conventions, watchlist)
├── PROJECT_STATE.md        # current status + build plan
└── README.md
```

---

## Getting started

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
# Set QWEN_API_KEY (DashScope). To run keyless with mock fixtures, set USE_MOCK_LLM=true.
```

### 3. Run backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, API at `http://localhost:8000`.

---

## Agent society

```
                  ┌──────────────────┐
                  │      Trend       │
                  ├──────────────────┤
  ┌───────┐       │     Finance      │      ┌─────────┐    ┌───────────────┐    ┌──────────────────┐
  │ Scout │ ───►  ├──────────────────┤ ──►  │ Skeptic │ ─► │ Debate Engine │ ─► │      Chair       │
  └───────┘       │      Growth      │      └─────────┘    └───────────────┘    │ (venture_partner)│
                  │    Capability    │                                          └──────────────────┘
                  └──────────────────┘
   frame options   analyze (parallel)        stress-test      resolve conflicts       board memo
                                                               + dissent record

Scout → [Trend ∥ Finance ∥ Growth ∥ Capability] → Skeptic → Debate Engine → Chair
```

The analyst agents fan out concurrently via LangGraph (`asyncio.gather` + `asyncio.to_thread`);
every other stage runs sequentially on real data dependencies. **The Skeptic and the Debate Engine
are the centerpiece** — judging the decision *is* the product.

| Agent (`name` string) | Role | Output |
|-------|------|--------|
| **Scout** (`scout`) | Frames the options on the table | The options assessed |
| **Trend** (`trend`) | Reads market/demand signals for the decision | Market read |
| **Finance** (`finance`) | Models the decision vs company economics | Financial view |
| **Growth** (`growth`) | How the company executes | Go-to-market read |
| **Skeptic** (`skeptic`) | Attacks the weakest assumptions | Risk + failure modes |
| **Capability** (`capability`) | Scores organizational capability/readiness (rebuilt from founder-fit) | Readiness read |
| **Chair** (`venture_partner`) | Synthesizes the memo (canonical string stays `venture_partner`) | Board recommendation |

---

## Demo flow

1. Pick the company (stubbed picker → vault folder) and state one decision.
2. The council **selectively retrieves** the relevant notes from the company's vault.
3. Agents analyze in parallel; the Skeptic attacks the plan.
4. The Debate Engine surfaces conflicts; agents revise over rounds; unresolved conflicts become the **dissent record**.
5. The Chair writes the **board memo** (recommendation + confidence + missing inputs + phased plan).
6. The decision + memo are **written back to the vault**; a later outcome closes the loop.

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit `{ company_id, profile?, decision }`, get a `BoardResponse` |
| `GET` | `/api/response/{id}` | Fetch a board response |
| `POST` | `/api/feedback` | Write a decision outcome back to the vault |
| `GET` | `/api/company/{company_id}` | Get the company's decision history |

See [`docs/architecture.md`](docs/architecture.md) for the full request/response contract.

---

## Deploying

Backend runs on **Hugging Face Spaces** (Docker SDK, free CPU Basic) — a long-running container
holds the ~90–240s debate run that serverless can't, with no card required. Frontend runs on
**Vercel Hobby**, pointed at the backend via `NEXT_PUBLIC_API_BASE_URL`. A local + Cloudflare
Tunnel option is documented for live demos. Full steps, the Dockerfile spec, and the env-var
contract: **[`docs/deployment.md`](docs/deployment.md)**.

## Hackathon tracks

- **Primary:** Agent Society
- **Secondary:** MemoryAgent, Autopilot Agent
