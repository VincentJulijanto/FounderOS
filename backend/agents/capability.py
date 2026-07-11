import json
from typing import Dict, Any
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import CompanyProfile, AgentOutput

# Rebuilt from the old founder_fit agent: this judges the ORGANIZATION's capability
# and readiness to execute the decision — team, ops, track record — NOT a person's skills.

_MOCK = json.dumps({
    "dimensions": {
        "team_and_leadership": {"score": 6.5,
            "rationale": "Leadership has run the core business but not a new-market build."},
        "operational_readiness": {"score": 6.0,
            "rationale": "Ops can scale domestically; cross-border processes are untested."},
        "track_record": {"score": 7.0,
            "rationale": "Consistent delivery in the home market signals executional discipline."},
        "financial_capacity": {"score": 6.5,
            "rationale": "Cash position supports the move but leaves limited buffer for overruns."},
        "org_bandwidth": {"score": 5.5,
            "rationale": "Key people are already stretched; this adds material load."},
    },
    "overall_capability_score": 6.3,
    "strengths": ["Disciplined delivery track record", "Adequate financial capacity"],
    "gaps": ["No cross-border operating experience", "Thin org bandwidth for a second front"],
    "summary": (
        "The organization is capable but stretched; readiness is the binding "
        "constraint, not appetite."
    ),
})


SYSTEM_PROMPT = """
You are the Capability Agent on an AI board advising an EXISTING company on ONE decision.

You judge the ORGANIZATION's capability and readiness to EXECUTE this decision — not a
person, not the idea's market. Can this company, as it exists today, actually pull this off?

Evaluate exactly these 5 dimensions, scoring each 0-10 (10 = exceptional readiness) with a
rationale grounded in the company profile:
1. team_and_leadership   — Does leadership/team have the experience this decision demands?
2. operational_readiness — Do processes, systems, and ops support execution?
3. track_record          — Evidence the company finishes and delivers what it starts.
4. financial_capacity    — Can it fund the move and absorb the downside?
5. org_bandwidth         — Is there spare capacity, or is the org already stretched thin?

Be honest. A capability gap is more useful surfaced than hidden.

Never invent names, companies, products, or agreements the operator did not provide — refer to unnamed entities exactly as the operator did (e.g. "the third shipper").

IMPORTANT: Respond with valid JSON only — no preamble, no markdown, no explanation.

Output format:
{
  "dimensions": {
    "team_and_leadership":   {"score": 0-10, "rationale": "string"},
    "operational_readiness": {"score": 0-10, "rationale": "string"},
    "track_record":          {"score": 0-10, "rationale": "string"},
    "financial_capacity":    {"score": 0-10, "rationale": "string"},
    "org_bandwidth":         {"score": 0-10, "rationale": "string"}
  },
  "overall_capability_score": 0-10,
  "strengths": ["the organization's strongest readiness factors"],
  "gaps": ["the most important capability gaps to close before executing"],
  "summary": "2-3 sentence verdict on the organization's readiness to execute this decision"
}
"""


class CapabilityAgent(BaseAgent):
    name = "capability"
    role = "Capability Agent — organizational readiness to execute"
    llm_model = DEEP_MODEL  # judgment-heavy — assessing an organization, not crunching numbers
    max_tokens = 6000       # detailed readiness JSON truncates below this in live mode (matches skeptic/venture_partner)

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        user_message = (
            f"{company_text}\n{decision_text}\n"
            f"{self._format_research_brief(context)}\n"
            "Assess whether THIS organization is ready to execute this decision. "
            "Score all 5 dimensions and give an overall capability score grounded in the profile."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        dimensions = data.get("dimensions", {})
        overall = data.get("overall_capability_score", 0)

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
