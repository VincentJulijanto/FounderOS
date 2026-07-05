import json
from typing import Dict, Any
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import CompanyProfile, AgentOutput

_MOCK = json.dumps({
    "critical_assumption": (
        "That the two anchor customers' demand is durable enough to justify fixed commitment "
        "in a new market."
    ),
    "failure_modes": [
        {"risk": "Anchor demand evaporates after year one", "probability": "Medium",
         "mitigation": "Structure minimum-volume commitments before committing capital."},
        {"risk": "Local execution costs run 30-50% over plan", "probability": "Medium",
         "mitigation": "Pilot asset-light before any subsidiary build."},
    ],
    "steelman_against": "The reversible, asset-light option preserves optionality at low cost.",
    "risk_score": 6.0,
    "verdict": "PROCEED_WITH_CAUTION",
    "overall_concern": (
        "The decision's weakest point is betting fixed cost on demand that has "
        "not been contractually secured."
    ),
})


SYSTEM_PROMPT = """
You are the Skeptic on an AI board advising an EXISTING company on ONE decision. You are the
MAIN EVENT: judging this decision well IS the product.

Attack the decision's weakest assumptions and most likely failure modes. You are not
pessimistic for its own sake — you are rigorous. Pressure-test the options the other agents
are leaning toward. Name the single most dangerous assumption, the failure modes with
probabilities, and steelman the case AGAINST proceeding.

Never invent names, companies, products, or agreements the operator did not provide — refer to unnamed entities exactly as the operator did (e.g. "the third shipper").

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "critical_assumption": "the biggest assumption that could be wrong",
  "failure_modes": [
    {"risk": "string", "probability": "High|Medium|Low", "mitigation": "string"}
  ],
  "steelman_against": "the strongest case against proceeding as proposed",
  "risk_score": 0-10,
  "verdict": "PROCEED | PROCEED_WITH_CAUTION | AVOID",
  "overall_concern": "the single biggest concern the board must not ignore"
}
"""


class SkepticAgent(BaseAgent):
    name = "skeptic"
    role = "Skeptic — attacks the decision's weak points"
    llm_model = DEEP_MODEL  # needs careful reasoning to challenge assumptions
    max_tokens = 6000       # detailed failure-mode JSON truncates at the 2000 default in live mode

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        # Reality-check the analysts' reads if they ran before the Skeptic.
        analyst_context = context.get("analyst_summary", "")
        analyst_block = f"\n## What the analysts concluded\n{analyst_context}\n" if analyst_context else ""

        user_message = (
            f"{company_text}\n{decision_text}\n"
            f"{analyst_block}\n"
            "Attack this decision. Name the most dangerous assumption, the likely failure "
            "modes, and the strongest case against proceeding. Don't hold back."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        high_risks = [
            f["risk"] for f in data.get("failure_modes", [])
            if str(f.get("probability", "")).lower() == "high"
        ]
        concerns = high_risks or [f.get("risk", "") for f in data.get("failure_modes", [])]

        risk_score = data.get("risk_score", 5) or 5

        # The verdict arrives as a machine enum (PROCEED_WITH_CAUTION) in both mock
        # and live JSON; the memo shows it as prose.
        verdict = str(data.get("verdict") or "").replace("_", " ").strip().capitalize()

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("overall_concern", ""),
            score=round(10 - float(risk_score), 1),  # invert: high score = low risk
            key_findings=[
                f"Critical assumption: {data.get('critical_assumption', '')}",
                f"Case against: {data.get('steelman_against', '')}",
            ],
            concerns=concerns + ([f"Verdict: {verdict}"] if verdict else []),
            recommendations=[verdict] if verdict else [],
            raw_data=data,
        )
