# Board vs single-agent baseline — countable dimensions

Same decision, two paths: full 7-agent board (`/api/analyze`, live) vs one bare `qwen-plus` call with an equivalent advisor prompt. Counts only; no human judgment.

| Dimension (want) | harborline-scaling board | bare | bakery-central-kitchen board | bare | itservices-fixed-price board | bare | total board | total bare |
|---|---|---|---|---|---|---|---|---|
| Distinct risks identified (higher) | 3 | 4 | 3 | 0 | 3 | 0 | **9** | **4** |
| Missing inputs / unknowns named (higher) | 4 | 4 | 4 | 4 | 3 | 4 | **11** | **12** |
| Dissent / counter-arguments surfaced (higher) | 0 | 1 | 4 | 0 | 3 | 2 | **7** | **3** |
| Options assessed with verdicts (higher) | 2 | 1 | 4 | 1 | 4 | 1 | **10** | **3** |
| Concrete reversal conditions (higher) | 1 | 1 | 1 | 1 | 1 | 1 | **3** | **3** |
| Invented proper nouns (entities) (lower) | 1 | 42 | 5 | 65 | 1 | 40 | **7** | **147** |
| Confidence calibration present (higher) | 1 | 0 | 1 | 0 | 1 | 0 | **3** | **0** |

- case1 (harborline-scaling): board 80s, bare 35s; invented nouns board=['Agent'], bare=['Advisory', 'Allocation', 'April', 'Architect', 'Bai', 'Change', 'Closer', 'Commercial', 'Committed', 'Committee', 'Considered', 'Cross', 'Diluting', 'Director', 'FTEs', 'Gate', 'High', 'Hybrid', 'Lane', 'Lang', 'Lead', 'Leadership', 'Misses', 'Moc', 'Operations', 'Owner', 'Path', 'Preemptively', 'Recommended', 'Rejected', 'Root', 'Scaling', 'Solutions', 'Son', 'Spend', 'Steering', 'Straining', 'TEUs', 'Thought', 'Vietnamese', 'Were', 'Where']
- case2 (bakery-central-kitchen): board 120s, bare 38s; invented nouns board=['Gate', 'Readiness', 'Round', 'Scale', 'YoY'], bare=['Accept', 'Ambassador', 'Analysis', 'April', 'Bar', 'Brand', 'Cease', 'Change', 'Close', 'Commit', 'Cons', 'Considered', 'Consolidation', 'Convert', 'Current', 'Design', 'Director', 'Efficiency', 'Enterprise', 'Exit', 'Factor', 'Finalise', 'Fit', 'Food', 'Full', 'Grant', 'Guarantee', 'High', 'Hybrid', 'Innovation', 'Internal', 'Lab', 'Leadership', 'Leads', 'Leases', 'Likelihood', 'Low', 'Marketing', 'Medium', 'Metrics', 'Mitigations', 'Momentum', 'One', 'Optimal', 'Owner', 'Partial', 'Path', 'Position', 'Practice', 'Prep', 'Pros', 'Put', 'Rejected', 'Resilience', 'Sales', 'See', 'Shift', 'Singapore', 'Stay', 'Strategic', 'Strategy', 'Tasting', 'Train', 'Two', 'Were']
- case3 (itservices-fixed-price): board 22s, bare 34s; invented nouns board=['Gate'], bare=['Advisory', 'Agile', 'Balances', 'Change', 'Charter', 'Cons', 'Considered', 'Control', 'Delivery', 'Director', 'Excellence', 'Feb', 'Group', 'High', 'Increases', 'June', 'Lead', 'Leadership', 'Likelihood', 'Loses', 'Low', 'Mar', 'Medium', 'Metric', 'Mitigations', 'Offers', 'Owner', 'PMs', 'Pricing', 'Pros', 'Report', 'Requires', 'SOWs', 'Sales', 'Secondary', 'Signals', 'Signed', 'Strategy', 'Success', 'Unacceptable']

**Counter caveat:** the invented-noun heuristic over-counts Title-Case heading vocabulary
(Pros/Cons/Likelihood/Owner/month names) on the bare side — those are formatting, not entities.
After discounting them by hand, the honest count is: board **0 real invented entities** across all
three cases (its 7 hits are generic words), bare **several real fabrications** — e.g. case 1 names
the "Moc Bai" and "Lang Son" border crossings and invents a "Solutions Architect"/steering-committee
org structure the input never mentioned. Directionally the dimension stands; the raw numbers overstate it.

**Fairness notes:** case 1 gives the board its vault memory (5 seed notes) — that's the product,
but it is an advantage the bare call lacks; cases 2-3 are cold starts for both. Case 3's board run
(22s) was partially served by the in-process provider cache after an earlier timed-out attempt
(machine slept mid-run); outputs are identical to a fresh run by construction (full-prompt cache key).
