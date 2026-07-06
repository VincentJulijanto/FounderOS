# FounderOS — 3-minute demo script

**Target duration:** 3 minutes
**Track:** Agent Society (primary), MemoryAgent + Autopilot (secondary)

## Before the slot (morning-of ritual, ~15 min)
1. Hit GET / on the Space (wakes it if asleep), confirm llm_mode: live.
2. One warm-up decision on a seed company (confirms pipeline, warms everything).
3. RESTART the Space from its settings — factory-resets the vault to pristine seed.
4. Open two tabs: Tab A = founderos-zeta.vercel.app (landing), Tab B = /boardroom.
5. Kestrel receipt ready (recorded cold-start proof + vault folder timestamps).
6. Check DashScope quota. Local backup (npm run dev + local backend) idling but ready.

## 0:00-0:25 — Open live, start the clock
Tab B. + New company, a rehearsed two-line profile (name every entity explicitly — never "our
partner"), one-line decision, no options. Convene the board. Say:
"FounderOS is an AI board for people who already run a business. I've just given it a company
it has never seen and one real decision — seven agents are now debating it live. That takes
about two minutes, so while the board argues, let me show you what it looks like when the
board knows you."

## 0:25-2:10 — The payoff: Harborline
Tab A → boardroom. Seed company, decision: "Should we scale the Vietnam cross-border lane
beyond the pilot?" with the two rehearsed options. Narrate the debate view while it runs:
"Harborline has a history with this board — prior decisions in its vault, including a Vietnam
pilot that hit sixty percent of plan. Watch the memo: the board doesn't start cold."
When the memo lands, point at three things in order:
- "Board memory consulted: N prior decisions" — "it read its own history before answering."
- The dissent section — "disagreement is the product. The Skeptic's objection is on the
  record, not buried."
- The money line — the memo citing the pilot's shortfall or board precedent: "no one told it
  that today — it remembered."

## 2:10-2:40 — The receipt
"Fair question: does that memory work for a company that isn't pre-loaded? Here's this
morning's proof —"
Show the Kestrel receipt: cold-start run, _profile.md + decision note born in the vault,
second run citing the first. Timestamped, unedited.

## 2:40-3:00 — Close the loop
Tab B — the 0:00 cold-start has finished. Show the fresh memo, then click Download PDF:
"Started from nothing three minutes ago, deployed on a free stack, about two cents a run. It
exports as a board-ready PDF — and the decision it just made is already written to its vault.
Next time this company asks, the board remembers."

## Q&A pocket answers
- "Is this live?" → "Everything you watched ran live against Qwen — both runs, on stage. The
  seed company's history was preloaded so you could see year-two memory in three minutes; the
  cold start proves day one."
- "Where does market/financial data come from?" → "The connector interface is built — Finance
  pulls a book-financials snapshot over MCP; in this build it's a deterministic stub, and
  wiring Xero or Shopify live is the same interface."
- "What if it's wrong?" → point at the memo: missing_inputs, what-would-change-this-call, the
  disclaimer. "The board tells you what it doesn't know. That's the product."

## Go/no-go (locked)
Deployed stack misbehaves morning-of → local backend + frontend, same script. Live Qwen down →
architecture walkthrough + receipt recording. Never mock on stage.
