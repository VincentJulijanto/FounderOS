import copy
import json
import re
from typing import Dict, Any, List
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import UserProfile, AgentOutput, StartupIdea, ExecutionPlan, LeanCanvas

# ── Base mock — the no-memory (first-session) recommendation ───────────────────
# Kept as a plain dict so the memory-aware path can derive variants from it via
# deepcopy. json.dumps(_BASE_RECOMMENDATION) is the exact byte-for-byte output a
# first-time founder gets, so anything the memory loop changes is provably the
# memory's doing and nothing else.
_BASE_RECOMMENDATION = {
    "top_ideas": [
        {
            "name": "AI Study Buddy",
            "tagline": "Your AI tutor, always available",
            "description": "Personalised AI tutoring app for university students",
            "target_market": "University students in Singapore",
            "startup_score": 7.5,
            "feasibility_score": 8.0,
            "market_attractiveness_score": 7.8,
            "founder_fit_score": 8.2,
            "risk_score": 3.5,
            "revenue_potential": "SGD 2,000–5,000/month by month 3",
            "estimated_monthly_revenue": "SGD 2000 by month 3",
            "time_to_launch": "3 weeks",
            "initial_investment": "SGD 300",
            "risk_level": "Low",
        }
    ],
    "execution_plan": {
        "startup_name": "StudyAI",
        "value_proposition": "Instant personalised academic help — any subject, any time",
        "customer_persona": "Alex, 20, NUS CS student. Pain: expensive tutors. Goal: ace exams affordably.",
        "lean_canvas": {
            "problem": "Tutors are expensive. Office hours are limited.",
            "solution": "AI tutor trained on university syllabi, available 24/7",
            "unique_value_proposition": "Your personal AI tutor at SGD 9/month",
            "unfair_advantage": "Deep integration with NUS/NTU module structures",
            "customer_segments": "University students in Singapore",
            "key_metrics": "DAU, session length, module coverage %",
            "channels": "Campus ambassadors, TikTok, Reddit communities",
            "cost_structure": "API costs SGD 50/mo, hosting SGD 20/mo",
            "revenue_streams": "Monthly subscription SGD 9/student",
        },
        "mvp_scope": "Web app: upload lecture notes, ask questions, get AI answers with citations",
        "landing_page_copy": "Struggling with your modules? Get instant AI help tailored to your syllabus.",
        "marketing_strategy": "Week 1-2: Campus ambassador at NUS/NTU. Week 3-4: TikTok study-tip content.",
        "customer_acquisition_plan": "Offer 7-day free trial via QR codes placed at university libraries.",
        "elevator_pitch": "StudyAI gives every student a personal AI tutor for less than a coffee per week.",
        "customer_outreach_templates": {
            "cold_email": "Hi [Name], struggling with [Module]? StudyAI gives instant explanations tailored to your syllabus.",
            "linkedin_dm": "Hey! I built an AI tutor for NUS/NTU students. Want free access for a week?",
            "cold_call_script": "Hi, I am building an AI study tool for students — can I get 2 minutes of your time?",
        },
        "thirty_day_roadmap": [
            "Week 1: Build MVP — note upload + Q&A interface",
            "Week 2: Recruit 10 beta testers from your own faculty",
            "Week 3: Collect feedback, fix top 3 issues, launch campus ambassador program",
            "Week 4: First paid conversion push — email beta users with limited-time discount",
        ],
    },
    "final_memo": "MOCK MODE ACTIVE — Add QWEN_API_KEY to .env and set USE_MOCK_LLM=false for real AI recommendations.",
    "founder_fit_rationale": "Technical background aligns well with AI tool development.",
    "key_risks_to_watch": ["API cost scaling", "Student willingness to pay", "Competition from free tools"],
}

_MOCK = json.dumps(_BASE_RECOMMENDATION)


# ── Memory-aware mock fixtures (Phase 5 memory loop) ───────────────────────────
# Mirrors Phase 4's stage-specific mock-conflict path: in mock mode the VP output
# must OBSERVABLY change when the founder has prior history, or the memory loop is
# invisible without a live key. The headline behaviour: when memory shows an
# ABANDONED venture, steer the #1 pick AWAY from that heavy build toward a
# service-first, faster-time-to-value, lower-commitment idea — and say so in the
# memo. The abandoned AI study-app direction is demoted to a #2 fallback, not
# re-recommended. This is the keyless proof of the loop influencing recommendations.

_LEAN_PIVOT_IDEA = {
    "name": "Cohort Cram Sessions",
    "tagline": "Paid live exam-prep cohorts — earn before you build",
    "description": (
        "Service-first exam prep: run small paid live cram cohorts for specific "
        "NUS/NTU modules. No app to build, revenue in week one — a deliberately "
        "lower-commitment direction after a heavier build was abandoned."
    ),
    "target_market": "Exam-stressed NUS/NTU students in high-fail-rate modules",
    "startup_score": 7.0,
    "feasibility_score": 9.2,
    "market_attractiveness_score": 7.0,
    "founder_fit_score": 8.2,
    "risk_score": 2.0,
    "revenue_potential": "SGD 1,500–3,000/month by month 2",
    "estimated_monthly_revenue": "SGD 1500 by month 2",
    "time_to_launch": "1 week",
    "initial_investment": "SGD 50",
    "risk_level": "Low",
}

_LEAN_PIVOT_PLAN = {
    "startup_name": "CramCohort",
    "value_proposition": "Pass your hardest module with a small paid live cohort — no software required to start",
    "customer_persona": "Priya, 21, NTU engineering student. Pain: panics before finals, generic YouTube misses her syllabus. Goal: structured, accountable prep.",
    "lean_canvas": {
        "problem": "Students cram alone and panic; 1-on-1 tutoring is expensive.",
        "solution": "Small paid live cram cohorts per module over video, capped at 8 seats.",
        "unique_value_proposition": "Module-specific group cram for the price of one coffee per session.",
        "unfair_advantage": "You've taken these exact modules and know what gets tested.",
        "customer_segments": "NUS/NTU students in high-fail-rate modules.",
        "key_metrics": "Seats sold per cohort, repeat-booking rate, referral rate.",
        "channels": "Course Telegram groups, faculty WhatsApp, word of mouth.",
        "cost_structure": "Zoom SGD 20/mo; near-zero variable cost.",
        "revenue_streams": "Per-seat ticket SGD 25–40 per cram session.",
    },
    "mvp_scope": "A Telegram post + payment link + one scheduled Zoom cohort for a single module.",
    "landing_page_copy": "Finals in 2 weeks? Join a small live cram cohort for your exact module. 8 seats only.",
    "marketing_strategy": "Week 1: post in 5 module Telegram groups, fill one cohort. Then repeat per module and collect testimonials.",
    "customer_acquisition_plan": "DM classmates in your hardest module; offer the first cohort at SGD 15 to seed reviews.",
    "elevator_pitch": "CramCohort runs small paid live cram sessions for the exact modules students fear — revenue in week one, no app required.",
    "customer_outreach_templates": {
        "cold_email": "Hi [Name], running a live cram cohort for [Module] before finals — 8 seats, SGD 25. Want in?",
        "linkedin_dm": "Hey! Hosting a small live cram session for [Module]. Keen to join or share with your cohort?",
        "cold_call_script": "Hi, I run focused live cram sessions for [Module] — can I tell you about the next one in 60 seconds?",
    },
    "thirty_day_roadmap": [
        "Week 1: Pick the highest-pain module; sell 8 seats; run cohort 1.",
        "Week 2: Collect testimonials; open 2 more module cohorts.",
        "Week 3: Add a second time slot; introduce a 3-session bundle.",
        "Week 4: Decide which modules to productise into recorded mini-courses.",
    ],
}


def _read_memory_signals(memory_block: str) -> Dict[str, Any]:
    """
    Pull the few signals the keyless mock acts on out of the memory_context block
    (the same string MemoryStore.build_context produces). Deterministic, no LLM.
    """
    text = memory_block.lower()
    # Episodic lines: "Recommended 'X' (score 7.5). Outcome: abandoned."
    abandoned_ideas = re.findall(
        r"Recommended '([^']+)'.*?Outcome:\s*abandoned", memory_block
    )
    return {
        "present": bool(memory_block.strip()),
        "has_abandonment": "abandon" in text,
        "abandoned_ideas": abandoned_ideas,
        "launched": "has launched" in text or "outcome: launched" in text,
        "prefers_b2b": "b2b" in text,
    }


def _apply_abandonment_steer(data: Dict[str, Any], sig: Dict[str, Any]) -> Dict[str, Any]:
    """Promote the lean service-first pivot to #1; demote the abandoned direction."""
    names = sig["abandoned_ideas"]
    abandoned_str = ", ".join(f"'{n}'" for n in names) if names else "a prior venture"

    demoted = copy.deepcopy(data["top_ideas"][0])
    demoted["description"] = (
        "Deprioritised to #2 — the heavier AI study-app direction the founder has "
        "tried before; pursue only after the leaner pick proves demand. "
        + demoted["description"]
    )
    data["top_ideas"] = [copy.deepcopy(_LEAN_PIVOT_IDEA), demoted]
    data["execution_plan"] = copy.deepcopy(_LEAN_PIVOT_PLAN)
    data["final_memo"] = (
        f"Memory-informed recommendation. This founder previously abandoned "
        f"{abandoned_str}, so FounderOS deliberately does NOT re-recommend another "
        f"heavy build in that direction. The #1 pick is now a service-first "
        f"'{_LEAN_PIVOT_IDEA['name']}' that earns revenue in week one with minimal "
        f"upfront commitment — matching the learned pattern that this founder favours "
        f"faster time-to-value. The earlier AI study-app idea is retained only as a "
        f"#2 fallback. [MOCK MODE — memory loop active]"
    )
    data["founder_fit_rationale"] = (
        "Service-first model ships in days and reuses the founder's lived exam "
        "experience — a deliberate fit for someone who has walked away from heavier "
        "builds before."
    )
    data["key_risks_to_watch"] = [
        "Seat fill rate per cohort",
        "Time cost of running live sessions",
        "Converting one-off attendees into repeat bookings",
    ]
    data["memory_informed"] = True
    data["memory_adjustments"] = [
        f"Steered #1 away from previously abandoned direction ({abandoned_str}).",
        f"Promoted lower-commitment '{_LEAN_PIVOT_IDEA['name']}' to the #1 slot.",
        "Demoted the AI study-app idea to a #2 fallback.",
    ]
    return data


def _apply_history_ack(data: Dict[str, Any], sig: Dict[str, Any]) -> Dict[str, Any]:
    """Memory present but no abandonment — lighter, still-observable adjustments."""
    notes: List[str] = []
    idea = data["top_ideas"][0]
    if sig["launched"]:
        idea["startup_score"] = 8.3
        idea["time_to_launch"] = "5 weeks"
        idea["initial_investment"] = "SGD 800"
        idea["risk_level"] = "Medium"
        data["execution_plan"]["mvp_scope"] = (
            "Expanded MVP: note upload + Q&A + spaced-repetition quizzes — scoped up "
            "to match a founder with a proven launch track record."
        )
        notes.append("Raised ambition/scope to match a proven launch track record.")
    if sig["prefers_b2b"]:
        idea["target_market"] = "University departments & student-org budgets (B2B)"
        data["execution_plan"]["lean_canvas"]["customer_segments"] = (
            "University departments and student organisations (B2B buyers)"
        )
        notes.append("Shifted target market toward the founder's demonstrated B2B preference.")
    if not notes:
        notes.append("Prior FounderOS history was taken into account.")
    data["final_memo"] = "Memory-informed recommendation. " + " ".join(notes) + " " + data["final_memo"]
    data["memory_informed"] = True
    data["memory_adjustments"] = notes
    return data


def _memory_aware_mock(memory_block: str) -> str:
    """
    Mock-mode VP output that visibly reflects the founder's memory. With no memory
    it returns the exact base fixture; with memory it returns a content-shifted
    recommendation. This is what makes the memory loop demonstrable keyless.
    """
    sig = _read_memory_signals(memory_block)
    if not sig["present"]:
        return _MOCK
    data = copy.deepcopy(_BASE_RECOMMENDATION)
    if sig["has_abandonment"]:
        return json.dumps(_apply_abandonment_steer(data, sig))
    return json.dumps(_apply_history_ack(data, sig))


SYSTEM_PROMPT = """
You are the Venture Partner at FounderOS — the final decision maker.

Your mission: Synthesize all agent analyses, incorporate debate outcomes, and produce:
1. A ranked list of top 3 startup recommendations
2. A complete execution plan for the #1 recommendation
3. An investment-style recommendation memo

You have access to outputs from: Scout, Trend Analyst, Finance, Growth, and Skeptic agents.
Your job is to weigh all perspectives fairly — including the Skeptic's concerns — and make
a balanced, high-conviction recommendation tailored to THIS specific founder.

You are also given the founder's MEMORY — their past FounderOS sessions and the insights
learned from them. Treat it as decisive context: do not re-recommend ideas the founder has
already abandoned, respect learned constraints/preferences, and adjust ambition to their
demonstrated execution track record. If memory says there is no prior history, ignore it.

Also assess Founder Fit:
- How well do their skills match the opportunity?
- Can they realistically execute given their constraints?
- What's their unfair advantage?

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "top_ideas": [
    {
      "name": "string",
      "tagline": "string",
      "description": "string",
      "target_market": "string",
      "startup_score": 0-10,
      "feasibility_score": 0-10,
      "market_attractiveness_score": 0-10,
      "founder_fit_score": 0-10,
      "risk_score": 0-10,
      "revenue_potential": "string",
      "estimated_monthly_revenue": "SGD X by month Y",
      "time_to_launch": "X weeks",
      "initial_investment": "SGD X",
      "risk_level": "Low|Medium|High"
    }
  ],
  "execution_plan": {
    "startup_name": "string",
    "value_proposition": "string",
    "customer_persona": "string (name, age, job, pain point, goal)",
    "lean_canvas": {
      "problem": "Top 3 problems",
      "solution": "Your solution",
      "unique_value_proposition": "Single clear message",
      "unfair_advantage": "Can't be easily copied",
      "customer_segments": "Target customers",
      "key_metrics": "Numbers that matter",
      "channels": "How you reach customers",
      "cost_structure": "Fixed and variable costs",
      "revenue_streams": "How you make money"
    },
    "mvp_scope": "What to build in 2 weeks",
    "landing_page_copy": "Full landing page copy with headline, subheadline, features, CTA",
    "marketing_strategy": "90-day marketing plan",
    "customer_acquisition_plan": "How to get first 10 paying customers",
    "elevator_pitch": "30-second pitch",
    "customer_outreach_templates": {
      "cold_email": "Template email to potential customers",
      "linkedin_dm": "LinkedIn outreach message",
      "cold_call_script": "Phone script opener"
    },
    "thirty_day_roadmap": [
      "Week 1: ...",
      "Week 2: ...",
      "Week 3: ...",
      "Week 4: ..."
    ]
  },
  "final_memo": "2-3 paragraph investment-style memo explaining why this idea for this founder",
  "founder_fit_rationale": "Why this founder can win",
  "key_risks_to_watch": ["risk 1", "risk 2", "risk 3"]
}
"""


class VenturePartnerAgent(BaseAgent):
    name = "Venture Partner"
    role = "Consensus & Final Recommendation"
    llm_model = DEEP_MODEL  # synthesis + full execution plan requires best model
    max_tokens = 6000       # full ranked ideas + execution plan JSON is large (was 4000; Sprint B)

    def _mock_response(self) -> str:
        # Memory-aware in mock mode: the recommendation shifts when prior history
        # exists. _memory_block is set by analyze() just before the LLM call.
        return _memory_aware_mock(getattr(self, "_memory_block", ""))

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        profile_text = self._format_profile(profile)

        # Compile all agent findings
        agent_summary = self._compile_agent_summary(context)
        debate_summary = context.get("debate_summary", "No debate conflicts identified.")

        # Memory loop (Phase 5): fold this founder's history + learned insights into
        # the prompt so prior outcomes actually steer the recommendation. Empty for
        # first-time founders, in which case we tell the VP there is no prior history.
        memory_context = (context.get("memory_context") or "").strip()
        memory_block = memory_context if memory_context else (
            "No prior FounderOS history for this founder — treat as a first session."
        )
        # Drive the keyless mock path: empty when there is no real history so the
        # mock returns the unchanged baseline; the raw memory_context otherwise.
        self._memory_block = memory_context

        user_message = (
            f"{profile_text}\n\n"
            f"=== Founder Memory (past sessions & learned insights) ===\n{memory_block}\n\n"
            f"=== Agent Analysis Summary ===\n{agent_summary}\n\n"
            f"=== Debate Outcome ===\n{debate_summary}\n\n"
            "Based on ALL of the above — and explicitly accounting for the founder's "
            "memory above — produce your final recommendation."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)  # uses class max_tokens (6000)
        data = self._parse_json(raw)

        # Founder-Fit is owned by the dedicated FounderFitAgent. Defer to its score
        # for the final field so the UI never shows two conflicting numbers; the VP's
        # own founder-fit prompt fragment stays as qualitative guidance only.
        ff_output = context.get("founder_fit_output")
        if ff_output is not None:
            for idea in data.get("top_ideas", []):
                idea["founder_fit_score"] = ff_output.score

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("final_memo", ""),
            score=data.get("top_ideas", [{}])[0].get("startup_score", 0) if data.get("top_ideas") else 0,
            key_findings=[
                data.get("founder_fit_rationale", ""),
                f"Top pick: {data['top_ideas'][0]['name']}" if data.get("top_ideas") else "",
            ],
            concerns=data.get("key_risks_to_watch", []),
            recommendations=[idea["name"] for idea in data.get("top_ideas", [])[:3]],
            raw_data=data,
        )

    def _compile_agent_summary(self, context: Dict[str, Any]) -> str:
        """Format all agent outputs into a readable summary for the VP."""
        lines = []

        if context.get("scout_output"):
            s = context["scout_output"]
            lines.append(f"SCOUT: Found {len(s.recommendations)} opportunities. Top pick: {s.recommendations[0] if s.recommendations else 'N/A'}")

        if context.get("trend_output"):
            t = context["trend_output"]
            lines.append(f"TREND ANALYST (score {t.score}/10): {t.analysis[:200]}")
            lines.append(f"  Key findings: {'; '.join(t.key_findings[:2])}")

        if context.get("finance_output"):
            f = context["finance_output"]
            lines.append(f"FINANCE (score {f.score}/10): {f.analysis[:200]}")
            if f.concerns:
                lines.append(f"  Concerns: {f.concerns[0]}")

        if context.get("growth_output"):
            g = context["growth_output"]
            lines.append(f"GROWTH (score {g.score}/10): {g.analysis[:200]}")

        if context.get("skeptic_output"):
            sk = context["skeptic_output"]
            lines.append(f"SKEPTIC: {sk.analysis[:200]}")
            if sk.concerns:
                lines.append(f"  Top concerns: {'; '.join(sk.concerns[:2])}")

        if context.get("founder_fit_output"):
            ff = context["founder_fit_output"]
            lines.append(f"FOUNDER-FIT (canonical score {ff.score}/10): {ff.analysis[:200]}")
            lines.append(f"  Use {ff.score}/10 as the founder_fit_score for every idea.")

        return "\n".join(lines) if lines else "No agent outputs available."

    def build_structured_recommendation(self, raw_data: Dict[str, Any], profile: UserProfile):
        """
        Convert the VP's raw JSON into structured StartupIdea + ExecutionPlan objects.
        Called by the debate engine / graph after analyze().
        """
        top_ideas_raw = raw_data.get("top_ideas", [])
        exec_raw = raw_data.get("execution_plan", {})
        lean_raw = exec_raw.get("lean_canvas", {})

        top_ideas = [
            StartupIdea(
                name=idea.get("name", ""),
                tagline=idea.get("tagline", ""),
                description=idea.get("description", ""),
                target_market=idea.get("target_market", ""),
                startup_score=idea.get("startup_score", 0),
                feasibility_score=idea.get("feasibility_score", 0),
                market_attractiveness_score=idea.get("market_attractiveness_score", 0),
                founder_fit_score=idea.get("founder_fit_score", 0),
                risk_score=idea.get("risk_score", 5),
                revenue_potential=idea.get("revenue_potential", ""),
                estimated_monthly_revenue=idea.get("estimated_monthly_revenue", ""),
                time_to_launch=idea.get("time_to_launch", ""),
                initial_investment=idea.get("initial_investment", ""),
                risk_level=idea.get("risk_level", "Medium"),
            )
            for idea in top_ideas_raw
        ]

        lean_canvas = LeanCanvas(
            problem=lean_raw.get("problem", ""),
            solution=lean_raw.get("solution", ""),
            unique_value_proposition=lean_raw.get("unique_value_proposition", ""),
            unfair_advantage=lean_raw.get("unfair_advantage", ""),
            customer_segments=lean_raw.get("customer_segments", ""),
            key_metrics=lean_raw.get("key_metrics", ""),
            channels=lean_raw.get("channels", ""),
            cost_structure=lean_raw.get("cost_structure", ""),
            revenue_streams=lean_raw.get("revenue_streams", ""),
        )

        execution_plan = ExecutionPlan(
            startup_name=exec_raw.get("startup_name", ""),
            value_proposition=exec_raw.get("value_proposition", ""),
            customer_persona=exec_raw.get("customer_persona", ""),
            lean_canvas=lean_canvas,
            mvp_scope=exec_raw.get("mvp_scope", ""),
            landing_page_copy=exec_raw.get("landing_page_copy", ""),
            marketing_strategy=exec_raw.get("marketing_strategy", ""),
            customer_acquisition_plan=exec_raw.get("customer_acquisition_plan", ""),
            elevator_pitch=exec_raw.get("elevator_pitch", ""),
            customer_outreach_templates=exec_raw.get("customer_outreach_templates", {}),
            thirty_day_roadmap=exec_raw.get("thirty_day_roadmap", []),
        )

        return top_ideas, execution_plan
