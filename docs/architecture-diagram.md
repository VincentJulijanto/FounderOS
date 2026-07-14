# FounderOS — System Architecture Diagram

## Two-Layer Agent Society

FounderOS operates two coordinated agent systems. The **Board** (8 agents) evaluates business decisions. The **Feedback Intelligence Council** (3 agents) stress-tests accumulated feedback from the vault — demonstrating measurable efficiency gains over single-agent analysis.

```mermaid
graph TD
    subgraph INPUT["INPUT"]
        A["Company Picker\n(stubbed → vault folder)"]
        B["Decision\n(one call per run)"]
        C["Vault Read\nLLM-driven note selection\n(no RAG / no embeddings)"]
    end

    subgraph BOARD["LAYER 1 — 8-AGENT BOARD (LangGraph)"]
        direction TB
        S["Scout\nFrames the options on the table"]
        R["Market Intelligence\nFetches real-world benchmarks\n(MCP: web / news / crunchbase)"]
        
        subgraph ANALYSTS["Parallel Analyst Fan-out (asyncio.gather)"]
            T["Trend Analyst\nMarket signals"]
            F["Finance Agent\nP&amp;L, unit economics"]
            G["Growth Agent\nExecution & GTM"]
            CAP["Capability Agent\nOrg readiness (rebuilt from founder_fit)"]
        end

        SK["Skeptic ← THE MAIN EVENT\nAttacks the decision's weak points"]
        DE["Debate Engine\nConflict detection → ≤3 rounds\nSeverity-weighted consensus\nUnresolved → dissent[ ]"]
        CH["Chair (venture_partner)\nWrites the BoardRecommendation memo"]
    end

    subgraph COUNCIL["LAYER 2 — FEEDBACK INTELLIGENCE COUNCIL (Track 3)"]
        direction TB
        FA["Feedback Analyst\nClusters vault feedback → ranked themes\n+ single-agent baseline summary"]
        FS["Feedback Skeptic\nChallenges for survivorship bias,\nscope creep, thesis misalignment"]
        FC["Feedback Chair\nAccepts / reframes / overrides\neach Skeptic challenge"]
        BC["Baseline Comparison\ncorrections_count = integer delta\n(council vs. single agent)"]
    end

    subgraph VAULT["VAULT (per-company Obsidian markdown)"]
        direction LR
        VR["vault.read\nLLM selects relevant notes\nfrom frontmatter index"]
        VW["vault.write_back\nAppends decision note\n+ outcome loop"]
        VF["read_feedback\nReturns type:feedback notes\nto the Council"]
    end

    subgraph OUTPUT["OUTPUT"]
        BR["BoardResponse\nagent_outputs[ ] + debate_rounds[ ]\n+ consensus + recommendation"]
        MEMO["BoardRecommendation\nproceed / hold / conditional\n+ dissent[ ] + phased execution plan\n+ what_would_change_this_call"]
        CB["CouncilBriefResponse\ncouncil_dialogue[ ] + themes[ ]\n+ baseline_comparison"]
    end

    subgraph DEPLOY["DEPLOYMENT"]
        FE["Frontend\nNext.js 14 / Vercel Hobby\nfounderos-zeta.vercel.app"]
        BE["Backend\nFastAPI / Hugging Face Spaces Docker\n(long-running: holds 90–240s debate)\nPort 7860"]
    end

    A --> C
    B --> C
    C --> VR
    VR --> S
    S --> R
    R --> ANALYSTS
    ANALYSTS --> SK
    SK --> DE
    DE --> CH
    CH --> VW
    CH --> BR
    BR --> MEMO

    VF --> FA
    FA --> FS
    FS --> FC
    FC --> BC
    BC --> CB

    FE <-->|NEXT_PUBLIC_API_BASE_URL| BE
    BE --> BOARD
    BE --> COUNCIL
    VAULT --> BE

    classDef layer1 fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    classDef layer2 fill:#3b1a2e,stroke:#ec4899,color:#e2e8f0
    classDef vault fill:#1a2e1a,stroke:#22c55e,color:#e2e8f0
    classDef io fill:#1a1a2e,stroke:#6366f1,color:#e2e8f0
    classDef deploy fill:#2e2a1a,stroke:#f59e0b,color:#e2e8f0

    class S,R,T,F,G,CAP,SK,DE,CH,ANALYSTS layer1
    class FA,FS,FC,BC layer2
    class VR,VW,VF vault
    class A,B,BR,MEMO,CB io
    class FE,BE deploy
```

## Track 3: Agent Society — How the Criteria Map

| Track 3 Criterion | FounderOS Implementation |
|---|---|
| **Task decomposition + role assignment** | 11 agents across 2 layers, each with a distinct system prompt and strict input/output shape |
| **Dialogue and negotiation** | `council_dialogue: CouncilTurn[]` — every agent's message is recorded and rendered in the UI |
| **Conflict resolution mechanisms** | Debate engine: conflict detection → revision rounds → severity-weighted consensus. Feedback Council: `overrides[]` records accepted / reframed / overridden per Skeptic challenge |
| **Measurable efficiency gain** | `baseline_comparison.corrections_count` — the integer delta between what a single agent reports and what the council catches |

## Cross-Track Elements

| Track | Element in FounderOS |
|---|---|
| **Track 1 — MemoryAgent** | The vault: per-company Obsidian markdown with LLM-driven selective retrieval. The board "remembers" prior decisions across sessions without loading the whole vault into context. |
| **Track 4 — Autopilot Agent** | The `execution_plan` in `BoardRecommendation`: a phased (Validate → Pilot → Scale) business workflow generated automatically from the board debate. |

## API Surface

```
POST /api/analyze          → BoardResponse       (the 8-agent board run)
GET  /api/response/{id}    → BoardResponse       (fetch saved run)
POST /api/feedback         → { status: "ok" }   (outcome loop → vault)
GET  /api/company/{id}     → vault index         (decision history)
POST /api/council-brief    → CouncilBriefResponse  (Track 3 council run)
```
