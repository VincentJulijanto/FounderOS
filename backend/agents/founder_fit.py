import json
from typing import Dict, Any
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import UserProfile, AgentOutput

_MOCK = json.dumps({
    "dimensions": {
        "founder_background": {
            "score": 8.0,
            "rationale": "CS background and coding skills map directly to building a software product.",
        },
        "domain_expertise": {
            "score": 6.5,
            "rationale": "Strong technical depth; less direct experience in the target customer's domain.",
        },
        "execution_history": {
            "score": 6.0,
            "rationale": "No prior launches on record, but available weekly hours support steady execution.",
        },
        "team_composition": {
            "score": 5.0,
            "rationale": "Solo founder — covers product/engineering but lacks a dedicated sales/marketing partner.",
        },
        "coachability": {
            "score": 7.5,
            "rationale": "Profile signals openness to feedback and iteration; no evidence of rigidity.",
        },
    },
    "overall_fit_score": 6.6,
    "strengths": [
        "Technical skills directly enable the MVP",
        "Genuine interest in the problem space",
    ],
    "gaps": [
        "No co-founder for go-to-market",
        "Unproven execution track record",
    ],
    "summary": "[MOCK] Founder-Fit analysis. Add QWEN_API_KEY for real results. Solid technical fit; main gap is distribution/team coverage.",
})


SYSTEM_PROMPT = """
You are the Founder-Fit Agent at FounderOS, an AI Venture Studio.

Your mission: Assess how well THIS specific founder is positioned to execute the proposed
startup opportunities. You are not judging the idea's market — other agents do that. You judge
the human: can this person realistically build and ship this venture?

Evaluate exactly these 5 dimensions, scoring each 0-10 (10 = exceptional fit) with a rationale:
1. founder_background  — Do their education, work history, and prior projects set them up to build this?
2. domain_expertise    — Do they understand the customer, problem, and industry being entered?
3. execution_history   — Is there evidence they can finish and ship? Past launches, consistency, follow-through.
4. team_composition    — Solo vs team. Are the critical roles (build, sell, operate) covered?
5. coachability        — Openness to feedback, willingness to iterate, self-awareness about gaps.

Be honest and specific. A weak founder-fit is more useful surfaced than hidden. Ground every
score in the founder's actual profile, not generic advice.

IMPORTANT: Respond with valid JSON only — no preamble, no markdown, no explanation.

Output format:
{
  "dimensions": {
    "founder_background": {"score": 0-10, "rationale": "string"},
    "domain_expertise":   {"score": 0-10, "rationale": "string"},
    "execution_history":  {"score": 0-10, "rationale": "string"},
    "team_composition":   {"score": 0-10, "rationale": "string"},
    "coachability":       {"score": 0-10, "rationale": "string"}
  },
  "overall_fit_score": 0-10,
  "strengths": ["the founder's strongest fit factors"],
  "gaps": ["the most important fit gaps to address"],
  "summary": "2-3 sentence overall verdict on this founder's fit for the opportunities"
}
"""


class FounderFitAgent(BaseAgent):
    name = "Founder-Fit Agent"
    role = "Founder Execution Fit Assessment"
    llm_model = DEEP_MODEL  # judgment-heavy — assessing a person, not crunching numbers

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: UserProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        opportunities = context.get("opportunities", [])
        profile_text = self._format_profile(profile)

        opp_list = "\n".join(
            f"- {opp['name']}: {opp.get('description', opp.get('tagline', ''))}"
            for opp in opportunities
        ) if opportunities else "Assess general fit for launching a startup."

        user_message = (
            f"{profile_text}\n\n"
            f"Assess this founder's fit to execute these opportunities:\n{opp_list}\n\n"
            "Score all 5 dimensions and give an overall fit score grounded in their profile."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        dimensions = data.get("dimensions", {})
        overall = data.get("overall_fit_score", 0)

        key_findings = [
            f"{dim.replace('_', ' ').title()}: {d.get('score', 'N/A')}/10"
            for dim, d in dimensions.items()
        ]

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("summary", ""),
            score=overall,
            key_findings=key_findings + [f"Strength: {s}" for s in data.get("strengths", [])],
            concerns=[f"Gap: {g}" for g in data.get("gaps", [])],
            recommendations=[],
            raw_data=data,
        )
