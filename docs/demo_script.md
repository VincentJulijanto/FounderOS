# FounderOS — Demo Script

**Target duration:** 3–5 minutes
**Track:** Agent Society (primary), MemoryAgent + Autopilot (secondary)

> Pivot framing: FounderOS is an **AI board/council** for operators of **existing businesses**.
> You bring **one decision**; seven agents evaluate it, debate it, and hand back a **board-ready
> memo** — a clear recommendation, the dissent behind it, what's missing, and a phased plan.

---

## Opening hook (30 seconds)

> "Every operator faces the same problem: a big decision — expand to a new market, launch a new
> tier, hire ahead of revenue — and no one in the room whose only job is to pressure-test it.
> Existing AI tools give you a confident answer and leave you to trust it.
>
> FounderOS is different. It's an AI board — **seven specialized agents that debate, challenge, and
> reach a verdict on your decision** — and it remembers your company from one meeting to the next."

---

## Step 1 — Bring a decision (30 seconds)

**Show:** Pick the company, then state the decision.

```
Company:   Meridian Logistics  (picked from the company list)
Sector:    Regional B2B logistics · Stage: scaling · Model: B2B SaaS + ops
Financials: ~SGD 4M ARR, ~30% gross margin, 14 months runway
Decision:  "Should we expand into Indonesia next quarter, or deepen in our home market first?"
Constraints: budget ~SGD 400k · timeline: decide within 3 weeks
```

> "Meridian is a scaling logistics company. They're weighing an Indonesia expansion against
> doubling down at home. Let's bring that decision to the board."

Click **"Convene the council →"**

---

## Step 2 — The council convenes (45 seconds)

**Show:** The council pulls the company's history from its vault, then the agents work.

> "First, the council reads Meridian's vault — its saved context and past decisions — and pulls in
> only what's relevant to *this* call. Then seven agents go to work:
> - The **Scout** frames the real options on the table
> - The **Trend** agent reads market and demand signals for Indonesia
> - The **Finance** agent models it against Meridian's actual economics
> - The **Growth** agent maps how they'd execute
> - The **Capability** agent asks whether the *organization* is ready to run two markets
> - And the **Skeptic** — this is the point — attacks the weakest assumptions in the plan"

---

## Step 3 — Conflict & debate (45 seconds)

**Show:** The debate view — conflicts surfacing, positions revised across rounds.

> "Here's where FounderOS is different from a single chatbot.
>
> The Trend agent likes the Indonesia timing. But the **Skeptic pushes back** — the org is stretched
> and the runway is tight. The **Finance** agent backs the Skeptic on cash. The **Growth** agent
> argues a phased pilot de-risks it.
>
> The agents **debate in rounds.** A moderator tracks each conflict until it resolves — or stays
> genuinely open. What doesn't resolve isn't hidden; it becomes the **dissent record** in the memo."

---

## Step 4 — The board memo (30 seconds)

**Show:** The board memo.

> "The **Chair synthesizes everything into a board memo:**
>
> Recommendation: **Conditional** — pilot Indonesia in one corridor before a full expansion.
> Confidence: **medium.**
> The **dissent** is on the page: the Skeptic's cash-runway objection, unresolved.
> **What's missing:** a landed-cost model and a local ops partner.
> **What would change this call:** 18+ months runway, or a signed anchor customer.
>
> Not just an answer — the reasoning, the disagreement, and what to do next."

---

## Step 5 — Phased execution plan (45 seconds)

**Show:** Click through the phased plan.

> "The memo carries a **phased execution plan** — not a generic to-do list:
>
> **Phase 1 — Validate:** landed-cost model, one Indonesian corridor, a local ops partner shortlist.
> **Phase 2 — Pilot:** run the single corridor, hold the home market steady.
> **Phase 3 — Scale (conditional):** expand only if the pilot clears the bar the memo names.
>
> Meridian goes from 'should we do this?' to 'here's the call, the risks, and the first phase' —
> in minutes."

---

## Step 6 — Memory / the vault (30 seconds)

**Show:** The company's decision history in the vault.

> "And FounderOS remembers. Every decision, its recommendation, and — later — how it actually turned
> out gets written back to Meridian's vault as a note.
>
> Next quarter, when Meridian weighs another market, the council retrieves *this* decision: what the
> Skeptic flagged, and what happened. The board gets smarter about *this specific company* every time
> it convenes — without ever loading the whole history into memory."

---

## Closing (30 seconds)

> "Traditional AI advisor: prompt → one confident answer. Done.
>
> FounderOS: your decision → a council → debate → a verdict with its dissent → a phased plan →
> written back to memory.
>
> This is what an Agent Society looks like pointed at a real business decision. We're not generating
> ideas — we're running a board."

---

## Judge Q&A prep

**Q: How is this different from ChatGPT?**
A: ChatGPT gives one answer. FounderOS runs **7 agents with opposing mandates** — the Skeptic's job
is to attack the plan the others back — and it debates to a verdict. The unresolved disagreement is
part of the output, not smoothed away.

**Q: Where does it get the right to advise on real money?**
A: It doesn't pretend to be a fiduciary board — the memo carries a one-line disclaimer, an explicit
`missing_inputs` list, and a `what_would_change_this_call` section. The operator owns the decision;
the council makes the trade-offs and the dissent legible.

**Q: Does the memory actually work?**
A: Yes. Company context is a per-company markdown vault. The council selectively retrieves only the
relevant notes for a decision (via an index of frontmatter + summaries — no vector DB), then writes
the decision and its later outcome back.

**Q: What's the latency?**
A: A full run is ~90–240s (7 agents + debate rounds). For demo, a pre-loaded result is ready as a
fallback.

---

## Demo day checklist

- [ ] Backend running (`uvicorn backend.main:app --reload`)
- [ ] Frontend running (`npm run dev`)
- [ ] `.env` with a valid `QWEN_API_KEY` (DashScope), or `USE_MOCK_LLM=true` to demo keyless
- [ ] A company vault pre-seeded (Meridian Logistics) with a couple of past decision notes
- [ ] Pre-loaded fallback memo in case of API issues
- [ ] Decision pre-filled to save time
- [ ] Browser full screen
