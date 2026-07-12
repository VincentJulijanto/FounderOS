# FounderOS — Submission (Track 3: Agent Society)

An AI board for people who already run a business: eight specialist agents that take one
decision ("is this sound, what are we missing?"), debate it live, and return a board-ready
memo — with dissent on the record, and a per-company memory that compounds across sessions.

**Try it:** https://founderos-zeta.vercel.app (live, free stack, ~2 minutes per board run)
**API:** https://vincent-playground-founderos-api.hf.space · **Repo:** this one.

## How it maps to the rubric

### Task decomposition & role assignment
Eight agents with disjoint mandates: Scout frames options; Market Intelligence gathers cited
market data before analysis; Trend/Finance/Growth/Capability analyze in parallel; the Skeptic's
only job is attack; the Chair synthesizes. Decomposition is structural, not cosmetic — see the
agent table in docs/architecture.md and the pipeline in backend/graph.py.

### Dialogue & negotiation
A Debate Engine detects conflicts between agent positions and runs rebuttal rounds; positions
revise under counterargument, and unresolved conflict ends the debate honestly rather than
being averaged away. Live exhibit of attributed positions in conflict, from a shipped memo:

> From a Harborline Logistics board run — "Should we scale the Vietnam cross-border lane beyond
> the pilot?":
> - **Growth:** "Commit to a full subsidiary now to capture anchor demand fast."
> - **Finance:** "The budget can't absorb subsidiary fixed cost without breaching the cash buffer."
>   → The board revised its position: go asset-light, scoped to a pilot — the capital-commitment
>   and timeline conflicts resolved.
> - **Skeptic:** "The anchor customers' LOIs aren't binding; demand may not survive year one."
> - **Trend:** "Regional demand signals and incumbent inertia support the expansion window."
>   → Unresolved across both rounds; shipped as the memo's dissent — both sides agree only signed
>   commitments settle it.

### Conflict resolution
Unresolved objections ship in the memo as an attributed dissent record, alongside "what would
change this call": the conditions under which the board reverses itself. The Chair adjudicates
with gating conditions ("proceed only if X and Y") — how real boards resolve.

### Measurable efficiency gain vs a single agent
We benchmarked the board against a single qwen-plus call with an equivalent prompt, on 3 live
decisions across 3 sectors (scripts/benchmark.py, raw outputs in scripts/bench_results/):

| Dimension | Board | Bare LLM |
|---|---|---|
| Distinct risks identified | 9 | 4 |
| Missing inputs named | 11 | 12 (tie) |
| Attributed dissent / counterarguments | 7 | 3 |
| Options assessed with verdicts | 10 | 3 |
| Reversal conditions | 3 | 3 (tie) |
| Fabricated entities (lower is better) | 0 real | invents border crossings, staff roles |
| Confidence calibration stated | 3/3 | 0/3 |

The honest rows: the bare model ties on naming unknowns and reversal conditions. Where the
structure wins is where structure should: dissent, per-option verdicts, calibrated confidence —
and fabrication, where the bare memo invented "Moc Bai" and "Lang Son" crossings and a
nonexistent Steering Committee while the board fabricated nothing. Fairness notes, including
counting caveats against ourselves, in scripts/bench_results/RESULTS.md. Cost: ~US$0.02 per
full board run.

### Memory: the board that remembers
Each company gets an Obsidian-style markdown vault — profile, every decision, its dissent, and
(when known) its outcome. Retrieval is LLM note-selection over an index (no vector DB);
write-back is automatic. Validated live: a cold-start company created through the UI received a
board run, and its second run cited the first decision's risks verbatim and hardened the
recommendation (validation reports in the repo history; archived write-backs in the project
receipts). Live memos cite cross-decision patterns ("the board has consistently rejected
irreversible actions") — pattern recall, not note lookup. The memo shows its provenance:
"Board memory consulted: N prior decisions."

### Trust posture
The memo tells you what it doesn't know: missing_inputs, what-would-change-this-call, a
fiduciary disclaimer, dissent on record. During live validation we caught the board fabricating
entity names ("ElecTech"), killed it at the prompt level, and verified the fix on the exact
trigger case. Mock output is disclosed three ways (response flag, on-screen badge, export
watermark). In live mode, the Market Intelligence agent refuses to invent numbers it could not
source — figures come back "not specified" rather than fabricated.

### Execution
Deployed end-to-end on a free stack (Vercel + HF Spaces Docker + Qwen via DashScope). Live runs
of 93-142s survive the HF proxy (four recorded
samples). Client-side PDF export of the memo, verified page-by-page. Env-configurable rate
limiting, input caps, vault path-traversal guards, and a dormant auth gate behind a feature
flag. 63 tests, hermetic keyless mock mode.
