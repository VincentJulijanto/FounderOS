# FounderOS — Track 3: Agent Society

An AI board for people who already run a business. You bring one decision — "is this sound,
what are we missing?" — and eight specialist agents evaluate it, debate their conflicts, and
return a board-ready memo with dissent on the record, reversal conditions, and per-company
memory that compounds across decisions.

**Live:** https://founderos-zeta.vercel.app · **API:** https://vincent-playground-founderos-api.hf.space

---

## Technical Depth & Engineering (30%)

**Qwen on Alibaba Cloud DashScope, two-tier model strategy.** Every agent inference is a Qwen
call through DashScope's OpenAI-compatible endpoint
(`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`, `backend/config.py`).
`backend/llm/provider.py` assigns tiers per agent class: `qwen-turbo` (`FAST_MODEL`) for the
parallel fan-out — Scout, Trend, Finance, Growth, the Research agent, and the three
feedback-council agents — and `qwen-plus` (`DEEP_MODEL`, env-overridable via `QWEN_MODEL`) for
the reasoning-heavy seats: Skeptic, Capability, Chair, the debate engine, and the SWE/QA pair.
The provider adds JSON-mode with a 3-attempt parse-retry loop (parse errors fed back to the
model) and an in-process response cache keyed on the full prompt.

**LangGraph orchestration.** `backend/graph.py` runs the pipeline: Scout frames options →
Research fetches real-world benchmarks → four analysts fan out in parallel → the debate engine
(`backend/consensus/debate_engine.py`) detects cross-agent conflicts and runs up to
`MAX_DEBATE_ROUNDS = 3` rebuttal rounds with explicit stop conditions (all-resolved, or a
zero-resolution stalemate round) — conflict status is final-round-authoritative, so a topic can
never read "resolved" while the last round shows it contested.

**Memory without a vector DB.** `backend/vault/store.py` implements per-company memory as a
plain markdown vault: a small index (frontmatter + one-line summaries) is handed to a
`qwen-turbo` call that selects which notes matter for the decision at hand — no embeddings, no
RAG stack. Company profiles hydrate from `_profile.md` on later runs, and every completed run
writes the decision + recommendation back, so the board's memory compounds.

**Production hardening.** Per-IP rate limits on every expensive route plus a global
shared-across-all-IPs backstop on the three LLM routes (`GLOBAL_LLM_RATE_LIMIT`, default
`60/hour;200/day`) so a rotating-IP bot cannot drain the model quota; `X-RateLimit-*` headers
on responses; all limits env-tunable (`backend/main.py`). Input length caps on every request
field (`backend/models.py`), path-traversal guard on vault access
(`backend/vault/store.py`), CORS pinned to the deployed frontend. A hermetic keyless mock mode
(every agent owns a deterministic fixture) keeps the full pipeline runnable with no API key;
**80 tests**, all green.

**Deployed, live end-to-end.** Vercel frontend + Docker backend on Hugging Face Spaces (the
long-running container holds the ~2-minute debate that serverless can't). A live board run
returns in ~128s with 8 agent outputs and 2 debate rounds.

## Innovation & AI Creativity (30%)

**The agent society applied to itself.** Beyond the board, FounderOS turns its agents on its
own product loop:

- *Feedback Intelligence Council* (`backend/consensus/feedback_council.py`): Analyst → Skeptic
  → Chair debate accumulated user feedback and produce a ranked product brief, with every turn
  recorded in an auditable dialogue.
- *Feature Delivery Loop* (`backend/consensus/feature_loop.py`): a Senior-SWE agent drafts a
  build spec from a validated theme, a QA agent reviews it, and the pair iterate for a bounded
  2 rounds (`QA_LOOP_ROUNDS`). Framed precisely: **it proposes specs; it does not write or
  ship code.** A passing spec is written to the vault as a release note for a human to act
  on — the loop has no shell, git, or network access by design (`backend/agents/swe.py`,
  `backend/agents/qa.py`).

**Honest-by-design memo.** Disagreement survives to the output instead of being averaged away:
the `BoardRecommendation` contract (`backend/models.py`) carries attributed `dissent[]`
(which agent, what position), `what_would_change_this_call` reversal conditions,
`missing_inputs[]` the board wishes it had, and a fiduciary disclaimer. The Research agent
reports `data_gaps` rather than fabricating benchmarks it cannot source
(`backend/agents/research.py`, `docs/agent-research.md`).

**Restraint as a feature.** The feature loop's signal gate declines to build on thin evidence:
given a theme backed by too few feedback notes, the live system returns
`insufficient_signal` with an LLM-written rationale ("only 3 feedback notes… too low to
represent the majority") instead of a spec (`backend/consensus/feature_loop.py`). An agent
that refuses work is rarer — and often more valuable — than one that always says yes.

## Problem Value & Impact (25%)

**Real pain.** Solo operators and small-business owners make irreversible calls — sign the
lease, hire the team, enter the market — with no board and no structured dissent. FounderOS
gives them a board's argument before commitment, at ~US$0.02 and ~2 minutes per decision.

**Measured against a single-agent baseline** — same three live decisions across three sectors
(logistics, F&B, IT services), full board vs one bare `qwen-plus` advisor call, counting only
what can be counted (`scripts/benchmark.py`, `scripts/bench_results/RESULTS.md`):

| Dimension | Board | Bare single agent |
|---|---|---|
| Distinct risks identified | **9** | 4 |
| Attributed dissent / counter-arguments | **7** | 3 |
| Options assessed with verdicts | **10** | 3 |
| Confidence calibration stated | **3/3** | 0/3 |
| Real fabricated entities (hand-verified) | **0** | several (invented border crossings, org roles) |
| Missing inputs named | 11 | 12 (honest tie) |
| Reversal conditions | 3 | 3 (honest tie) |

The results file counts caveats against ourselves: the raw invented-noun heuristic over-counts
the bare side's heading vocabulary, so the fabrication row uses the hand-discounted numbers.

**Memory compounds — validated live.** A second run on the same company hydrated the stored
profile, cited the first decision's risks in its memo, and hardened its recommendation
accordingly (`PROJECT_STATE.md`, walkthrough in `docs/demo_script.md`).

## Presentation & Documentation (15%)

- **Architecture diagram:** `docs/architecture.png` (rendered) — the current two-layer agent
  society (8-agent board + 3-agent council, model tiers, vault memory); Mermaid source in
  `docs/architecture-diagram.md`.
- **Demo video:** [Demo video (~2 min)](https://youtu.be/X6x_u6IWHog)
- **Guide:** this document plus `README.md` (quickstart, contract, project map) and
  `docs/architecture.md` (the frozen API contract).

## Proof of Alibaba Cloud Deployment

The backend's intelligence layer runs entirely on Alibaba Cloud: every agent inference is a
Qwen call via Alibaba Cloud's DashScope API
(`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`). Code-file proof:
[`backend/llm/provider.py`](https://github.com/VincentJulijanto/FounderOS/blob/main/backend/llm/provider.py)
(client + endpoint) and
[`backend/config.py`](https://github.com/VincentJulijanto/FounderOS/blob/main/backend/config.py)
(model tiers + base URL).

Backend deployed live on Alibaba Cloud ECS (Singapore, 47.236.142.171).

## Track

Track 3 — Agent Society.
