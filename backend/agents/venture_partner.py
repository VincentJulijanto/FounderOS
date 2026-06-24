from typing import Dict, Any, List
from .base import BaseAgent
from ..models import UserProfile, AgentOutput, StartupIdea, ExecutionPlan, LeanCanvas


SYSTEM_PROMPT = """
You are the Venture Partner at FounderOS — the final decision maker.

Your mission: Synthesize all agent analyses, incorporate debate outcomes, and produce:
1. A ranked list of top 3 startup recommendations
2. A complete execution plan for the #1 recommendation
3. An investment-style recommendation memo

You have access to outputs from: Scout, Trend Analyst, Finance, Growth, and Skeptic agents.
Your job is to weigh all perspectives fairly — including the Skeptic's concerns — and make
a balanced, high-conviction recommendation tailored to THIS specific founder.

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

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        profile_text = self._format_profile(profile)

        # Compile all agent findings
        agent_summary = self._compile_agent_summary(context)
        debate_summary = context.get("debate_summary", "No debate conflicts identified.")

        user_message = (
            f"{profile_text}\n\n"
            f"=== Agent Analysis Summary ===\n{agent_summary}\n\n"
            f"=== Debate Outcome ===\n{debate_summary}\n\n"
            "Based on ALL of the above, produce your final recommendation."
        )

        raw = self._call_claude(SYSTEM_PROMPT, user_message, max_tokens=4000)
        data = self._parse_json(raw)

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
