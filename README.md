# FounderOS – AI Venture Studio

> An AI-powered venture studio that uses a **society of specialized agents** to transform a founder's profile into a complete, validated startup execution plan.

---

## 🧠 What It Does

FounderOS takes a user's skills, budget, time, and goals — then deploys a multi-agent system that **scouts opportunities**, **debates assumptions**, **validates markets**, and **generates a full execution plan**.

**From:** `"I want to earn side income"`  
**To:** `"Here is your validated startup, lean canvas, and 30-day roadmap."`

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TailwindCSS |
| Backend | FastAPI (Python) |
| Agent Orchestration | LangGraph (parallel analyst fan-out) |
| AI Model | Qwen (qwen-turbo / qwen-plus via DashScope API) |
| Memory | PostgreSQL (SQLAlchemy async) |
| Semantic memory | Qwen embeddings persisted in PostgreSQL — no separate vector DB |

---

## 📁 Project Structure

```
founderos/
├── frontend/               # Next.js + Tailwind UI
│   └── src/
│       ├── app/            # Pages
│       └── components/     # ProfileForm, AgentDebate, StartupCard, ExecutionPlan
│
├── backend/
│   ├── agents/             # 7 specialized AI agents
│   │   ├── scout.py        # Opportunity Scout
│   │   ├── trend.py        # Trend Analyst
│   │   ├── finance.py      # Finance Analyst
│   │   ├── growth.py       # Growth Strategist
│   │   ├── skeptic.py      # Devil's Advocate
│   │   ├── founder_fit.py  # Founder-Fit Agent
│   │   └── venture_partner.py  # Final Decision Maker
│   │
│   ├── memory/
│   │   ├── episodic.py     # Past interactions (PostgreSQL)
│   │   └── semantic.py     # Learned user insights
│   │
│   ├── consensus/
│   │   └── debate_engine.py    # Conflict detection + debate rounds
│   │
│   ├── models.py           # Pydantic data models
│   ├── config.py           # Settings / env vars
│   ├── graph.py            # LangGraph orchestration
│   └── main.py             # FastAPI entry point
│
├── docs/
│   ├── architecture.md
│   ├── prd.md
│   └── demo_script.md
│
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your QWEN_API_KEY (DashScope) and DB connection
```

### 3. Run Backend

```bash
uvicorn main:app --reload --port 8000
```

### 4. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:3000`, API at `http://localhost:8000`.

---

## 🤖 Agent Society

### Pipeline

```
                  ┌──────────────────┐
                  │  Trend Analyst   │
                  ├──────────────────┤
  ┌───────┐       │ Finance Analyst  │      ┌─────────┐    ┌─────────────┐    ┌───────────────┐    ┌──────────────────┐
  │ Scout │ ───►  ├──────────────────┤ ──►  │ Skeptic │ ─► │ Founder-Fit │ ─► │ Debate Engine │ ─► │ Venture Partner  │
  └───────┘       │ Growth Strategist│      └─────────┘    └─────────────┘    └───────────────┘    └──────────────────┘
                  └──────────────────┘
   discover        analyze (parallel)        challenge        founder match       resolve conflicts      final decision

Scout → [Trend ∥ Finance ∥ Growth] → Skeptic → Founder-Fit → Debate Engine → Venture Partner
```

The three analyst agents (Trend, Finance, Growth) fan out concurrently via LangGraph
(`asyncio.gather` + `asyncio.to_thread`); every other stage runs sequentially on real
data dependencies.

| Agent | Role | Output |
|-------|------|--------|
| **Scout** | Discovers startup opportunities | 5 opportunity hypotheses |
| **Trend Analyst** | Evaluates market demand | Market attractiveness score |
| **Finance** | Estimates costs & revenue | Financial feasibility score |
| **Growth** | Plans acquisition strategy | Go-to-market plan |
| **Skeptic** | Challenges assumptions | Risk report |
| **Founder-Fit** | Scores founder–opportunity match across 5 dimensions | Founder-fit score |
| **Venture Partner** | Facilitates consensus & decides | Investment-style memo |

---

## 🎯 Demo Flow

1. User submits profile (skills, budget, hours, goals)
2. All agents analyze in parallel
3. Debate engine detects conflicts
4. Agents revise positions over 2–3 rounds
5. Venture Partner produces final recommendation
6. Execution plan auto-generated (lean canvas, roadmap, landing page copy)
7. Memory stores outcomes for future improvement

---

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Submit profile, get recommendation |
| `GET` | `/api/recommendation/{id}` | Fetch a recommendation |
| `POST` | `/api/feedback` | Submit outcome feedback |
| `GET` | `/api/memory/{user_id}` | Get user memory |

---

## 🏆 Hackathon Tracks

- **Primary:** Agent Society
- **Secondary:** MemoryAgent, Autopilot Agent
