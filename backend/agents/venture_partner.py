import json
from typing import Dict, Any, List
from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import (
    CompanyProfile,
    Decision,
    AgentOutput,
    BoardRecommendation,
    OptionAssessment,
    Dissent,
    ExecutionPlan,
    Phase,
    ConsensusReport,
)

# The Chair synthesizes the whole debate into the board memo. Canonical string stays
# `venture_partner`; the human-facing label is "Chair".

_MOCK = json.dumps({
    "recommendation": "conditional",
    "confidence": "medium",
    "rationale": (
        "[MOCK MODE — add QWEN_API_KEY for real results.] Proceed only on the asset-light path. "
        "The demand signal is real but the fixed-commitment option bets capital on demand that "
        "is not yet contractually secured. A reversible pilot captures most of the upside while "
        "the board's biggest unresolved concern — durable willingness to commit — is tested."
    ),
    "missing_inputs": [
        "Signed minimum-volume commitments from the anchor customers",
        "Bottom-up local operating-cost estimate",
        "Realistic ramp curve for the first three quarters",
    ],
    "options_assessed": [
        {"option": "Full subsidiary in the new market", "verdict": "avoid",
         "assessment": "Highest fixed cost and lowest reversibility for demand that is still assumed."},
        {"option": "Asset-light partnership with a local operator", "verdict": "favoured",
         "assessment": "Preserves optionality, tests demand cheaply, and fits the stated budget."},
        {"option": "Hold and deepen the current market", "verdict": "viable",
         "assessment": "Lowest risk; the fallback if the pilot's demand signal weakens."},
    ],
    "what_would_change_this_call": (
        "Signed volume commitments from both anchor customers, or a local cost base materially "
        "below plan, would move this from conditional to proceed on a larger footprint."
    ),
    "execution_plan": {
        "phases": [
            {"name": "Validate", "objective": "Contractually secure anchor demand",
             "actions": ["Convert LOIs into minimum-volume commitments",
                         "Bottom-up local cost model"], "timeframe": "0-6 weeks"},
            {"name": "Pilot", "objective": "Serve routes asset-light with a local 3PL",
             "actions": ["Sign a revocable partnership", "Run 2-3 live routes",
                         "Instrument unit economics"], "timeframe": "6-16 weeks"},
            {"name": "Scale", "objective": "Commit only on proven economics",
             "actions": ["Review pilot P&L against plan",
                         "Decide subsidiary vs. deepen-partnership"], "timeframe": "4-6 months"},
        ]
    },
    "financial_view": (
        "Affordable within the stated budget on the asset-light path, with margin compression "
        "for 2-3 quarters before payback. The subsidiary option would strain the cash buffer."
    ),
    "risks": [
        "Anchor demand proves softer than the LOIs suggest",
        "Local operating costs run over plan",
        "Org bandwidth is stretched across two fronts",
    ],
    "disclaimer": "Advisory output from an AI board, not a fiduciary board decision. The operator owns the call.",
})


SYSTEM_PROMPT = """
You are the CHAIR of an AI board of directors advising an EXISTING company on ONE decision.

You have the analyses of the whole board — Scout (options), Trend, Finance, Growth, Skeptic,
Capability — plus the debate outcome and any prior board history from the company's vault.
Your job: synthesize all of it into a board-ready memo that CONVERGES on a verdict.

Rules:
- Plain operator language. No consultant/McKinsey jargon.
- Be explicit about the limits of your confidence: list missing inputs, and state what would
  change the call. This is advice attached to real money.
- Assess EACH option on the table (one entry per option, 1:1).
- Give a phased execution plan (Validate → Pilot → Scale style), not a lean canvas.
- Take the vault history seriously if present: don't re-litigate settled calls; build on them.

IMPORTANT: Respond with valid JSON only.

Output format:
{
  "recommendation": "proceed | hold | conditional",
  "confidence": "low | medium | high",
  "rationale": "plain-language why this call",
  "missing_inputs": ["what you'd need to be more sure"],
  "options_assessed": [
    {"option": "string (matches an option on the table)", "assessment": "string",
     "verdict": "favoured | viable | avoid"}
  ],
  "what_would_change_this_call": "the conditions that flip the recommendation",
  "execution_plan": {
    "phases": [
      {"name": "Validate", "objective": "string", "actions": ["..."], "timeframe": "string"}
    ]
  },
  "financial_view": "plain-language financial read",
  "risks": ["risk 1", "risk 2"],
  "disclaimer": "one line — advisory, not a fiduciary board"
}
"""


class VenturePartnerAgent(BaseAgent):
    name = "venture_partner"                 # canonical string; displays as "Chair"
    role = "Chair — synthesizes the debate into the board memo"
    llm_model = DEEP_MODEL
    max_tokens = 6000                         # full memo JSON is large

    def _mock_response(self) -> str:
        return _MOCK

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        decision: Decision = context["decision"]
        company_text = self._format_company(profile)
        decision_text = self._format_decision(decision)

        agent_summary = self._compile_agent_summary(context)
        debate_summary = context.get("debate_summary", "No debate conflicts identified.")
        vault_block = context.get("vault_context") or (
            "No prior board history for this company — treat as a first session."
        )

        user_message = (
            f"{company_text}\n{decision_text}\n\n"
            f"=== Prior board history (vault) ===\n{vault_block}\n\n"
            f"=== Board analysis summary ===\n{agent_summary}\n\n"
            f"=== Debate outcome ===\n{debate_summary}\n\n"
            "Write the board memo. Converge on a verdict and be explicit about what's missing."
        )

        raw = self._call_llm(SYSTEM_PROMPT, user_message)
        data = self._parse_json(raw)

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=data.get("rationale", ""),
            score=None,
            key_findings=[
                f"Recommendation: {data.get('recommendation', 'conditional')} "
                f"({data.get('confidence', 'medium')} confidence)",
            ],
            concerns=data.get("risks", []),
            recommendations=[data.get("recommendation", "conditional")],
            raw_data=data,
        )

    def _compile_agent_summary(self, context: Dict[str, Any]) -> str:
        """Format the board's outputs into a readable summary for the Chair.

        Keyed by canonical agent-name strings (scout, trend, finance, growth,
        skeptic, capability).
        """
        outputs: Dict[str, AgentOutput] = context.get("agent_outputs", {})
        labels = {
            "scout": "SCOUT (options framing)",
            "trend": "TREND",
            "finance": "FINANCE",
            "growth": "GROWTH",
            "skeptic": "SKEPTIC (main event)",
            "capability": "CAPABILITY (org readiness)",
        }
        lines = []
        for key, label in labels.items():
            out = outputs.get(key)
            if not out:
                continue
            score = f" (score {out.score}/10)" if out.score is not None else ""
            lines.append(f"{label}{score}: {out.analysis[:220]}")
            if out.concerns:
                lines.append(f"  Concerns: {'; '.join(out.concerns[:2])}")
        return "\n".join(lines) if lines else "No agent outputs available."

    # ──────────────────────────────────────────
    # Build the structured BoardRecommendation (called by the graph after analyze)
    # ──────────────────────────────────────────

    def build_recommendation(
        self,
        raw_data: Dict[str, Any],
        decision: Decision,
        consensus: ConsensusReport | None = None,
    ) -> BoardRecommendation:
        """Convert the Chair's raw JSON into a BoardRecommendation.

        The dissent record is derived from the debate's UNRESOLVED conflicts (the
        auditable objections that did not get settled), merged with anything the
        Chair itself flagged. options_assessed maps 1:1 onto the decision options.
        """
        # Options assessed — ensure one entry per option on the table (1:1).
        chair_assessed: List[OptionAssessment] = [
            OptionAssessment(
                option=item.get("option", ""),
                assessment=item.get("assessment", ""),
                verdict=item.get("verdict"),
            )
            for item in raw_data.get("options_assessed", [])
            if isinstance(item, dict)
        ]
        decision_opts = decision.options or []
        overlap = {a.option for a in chair_assessed} & set(decision_opts)

        if decision_opts and not overlap and len(chair_assessed) == len(decision_opts):
            # The Chair assessed the options in order but under its own labels (common
            # in mock mode) — realign the assessments onto the operator's option strings.
            assessed = [
                OptionAssessment(option=opt, assessment=ca.assessment, verdict=ca.verdict)
                for opt, ca in zip(decision_opts, chair_assessed)
            ]
        else:
            assessed = chair_assessed
            covered = {a.option for a in assessed}
            for opt in decision_opts:
                if opt not in covered:
                    assessed.append(OptionAssessment(option=opt, assessment="Not separately assessed."))

        # Dissent — the unresolved conflicts become the auditable record.
        dissent: List[Dissent] = []
        seen = set()
        if consensus:
            for c in consensus.unresolved_conflicts:
                # Attribute to the agent who held the objection (prefer the skeptic side).
                agent = c.agent_a if "skeptic" in c.agent_a.lower() else c.agent_b
                position = c.agent_a_position if agent == c.agent_a else c.agent_b_position
                key = (agent, position)
                if key not in seen:
                    dissent.append(Dissent(agent=agent, position=position))
                    seen.add(key)
        for item in raw_data.get("dissent", []):
            if isinstance(item, dict):
                key = (item.get("agent", ""), item.get("position", ""))
                if key not in seen and key[1]:
                    dissent.append(Dissent(agent=item.get("agent", ""), position=item.get("position", "")))
                    seen.add(key)

        # Phased execution plan.
        phases_raw = (raw_data.get("execution_plan") or {}).get("phases", [])
        phases = [
            Phase(
                name=p.get("name", ""),
                objective=p.get("objective", ""),
                actions=p.get("actions", []),
                timeframe=p.get("timeframe"),
            )
            for p in phases_raw if isinstance(p, dict)
        ]

        return BoardRecommendation(
            recommendation=raw_data.get("recommendation", "conditional"),
            confidence=raw_data.get("confidence", "medium"),
            rationale=raw_data.get("rationale", ""),
            missing_inputs=raw_data.get("missing_inputs", []),
            options_assessed=assessed,
            dissent=dissent,
            what_would_change_this_call=raw_data.get("what_would_change_this_call", ""),
            execution_plan=ExecutionPlan(phases=phases),
            financial_view=raw_data.get("financial_view", ""),
            risks=raw_data.get("risks", []),
            disclaimer=raw_data.get(
                "disclaimer",
                "Advisory output from an AI board, not a fiduciary board decision. "
                "The operator owns the call.",
            ),
        )
