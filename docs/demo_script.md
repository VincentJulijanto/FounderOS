# FounderOS — Hackathon Demo Script

**Target duration:** 3–5 minutes  
**Track:** Agent Society (Primary), MemoryAgent + Autopilot (Secondary)

---

## 🎬 Opening Hook (30 seconds)

> "Every year, thousands of students and young professionals want to start something.
> But they don't know where to begin. Existing AI tools give you a list of ideas and 
> leave you stranded.
>
> FounderOS is different. It's an AI Venture Studio — where six specialized agents 
> **debate, challenge, and collaborate** to build your complete startup plan from scratch."

---

## 🧑 Step 1 — Profile Input (30 seconds)

**Show:** Fill in the profile form live.

```
Name: Alex Tan
Background: NUS Computer Science student, Year 2
Skills: Python, React, Data Analysis
Budget: SGD 500
Hours/week: 10
Interests: EdTech, Productivity, AI
Goals: Earn SGD 1,000/month side income within 3 months
```

> "Alex is a CS student at NUS. He has some coding skills, SGD 500, and 10 hours a week.
> Let's see what our agent society recommends."

Click **"Launch Agent Society →"**

---

## 🤖 Step 2 — Agent Society in Action (45 seconds)

**Show:** The agent analysis screen with agents activating one by one.

> "Six agents are now working in parallel:
> - The **Scout** is identifying market gaps matching Alex's profile
> - The **Trend Analyst** is evaluating market demand  
> - The **Finance Agent** is running financial projections
> - The **Growth Agent** is designing acquisition strategies
> - And the **Skeptic** — this is the key — is *challenging every assumption*"

---

## ⚡ Step 3 — Conflict & Debate (45 seconds)

**Show:** The debate screen activating with agent messages.

> "Here's where FounderOS is different from any other AI tool.
>
> The Scout found a strong opportunity in AI Study Tools.
> But the **Skeptic pushes back** — the market is crowded, students don't pay.
> 
> Now watch what happens: the agents **debate in real time.**
> The Growth Agent counters with a campus referral strategy.
> The Finance Agent validates the revenue model.
> 
> After 2 rounds of debate — consensus is reached."

---

## 🏆 Step 4 — Recommendation (30 seconds)

**Show:** The top 3 startup cards with scores.

> "The Venture Partner synthesises everything and produces an investment-style memo.
> 
> Alex's top recommendation: **[startup name]** — a [tagline].
> Startup score: 8.4. Feasibility: 7.9. Founder fit: 9.1.
> 
> Not just scores — the agents explain *why Alex specifically can win this.*"

---

## 📋 Step 5 — Autopilot Execution (45 seconds)

**Show:** Click through the execution plan tabs.

> "Now the Autopilot kicks in. FounderOS auto-generates everything Alex needs to launch:
>
> Here's Alex's **Lean Canvas** — problem, solution, channels, revenue model.
>
> Here's his **30-day roadmap** — week by week.
>
> Here's his **landing page copy** — ready to paste into Framer or Webflow.
>
> And here are his **customer outreach templates** — cold emails, LinkedIn DMs, already written.
>
> Alex goes from 'I want to earn side income' to 'I have a complete launch plan' — in under 2 minutes."

---

## 🧠 Step 6 — Memory (30 seconds)

**Show:** Briefly show the memory section or explain it.

> "FounderOS also learns. 
>
> If Alex comes back next month and says his tutoring startup didn't work out — 
> the system remembers. Episodic memory stores what was tried.
> Semantic memory extracts the insight: 'Alex prefers B2B over direct-to-consumer.'
>
> Every future recommendation gets smarter."

---

## 🚀 Closing (30 seconds)

> "Traditional AI startup generators: User → LLM → Generic idea. Done.
>
> FounderOS: User → Agent Society → Debate → Consensus → Memory → Full Execution Plan.
>
> This is what Agent Society looks like when applied to a real problem.
> We're not just generating content — we're running a venture studio."

---

## 💡 Judge Q&A Prep

**Q: How is this different from ChatGPT?**  
A: ChatGPT gives one response. FounderOS has 6 agents with opposing mandates — the Skeptic's job is to *challenge* the Scout. The conflict resolution is where the value comes from.

**Q: Does the memory actually work?**  
A: For the hackathon, memory is in-memory store. Production version uses PostgreSQL with SQLAlchemy. The semantic extraction via Claude is fully implemented.

**Q: Can it handle different user types?**  
A: Yes — we've tested with designers, marketers, non-technical users. The Founder Fit assessment ensures recommendations match actual skills.

**Q: What's the latency?**  
A: Full pipeline is ~45–90 seconds (6 LLM calls + debate rounds). For demo, can show pre-loaded result.

---

## 🔧 Demo Day Checklist

- [ ] Backend running locally (`uvicorn main:app --reload`)
- [ ] Frontend running (`npm run dev`)
- [ ] `.env` file with valid Anthropic API key
- [ ] Pre-loaded fallback result in case of API issues
- [ ] Profile form pre-filled with Alex's data (saves 30 seconds)
- [ ] Browser at full screen, dark mode
