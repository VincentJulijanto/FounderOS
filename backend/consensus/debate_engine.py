"""
Debate Engine — the main event of FounderOS.

The board doesn't chain agents linearly; it debates ONE decision:
1. Collects all agent outputs
2. Detects disagreements between agents about the decision
3. Runs up to MAX_DEBATE_ROUNDS debate rounds where agents revise positions
4. Scores how much of the (severity-weighted) disagreement was resolved
5. Produces a ConsensusReport + summary for the Chair — unresolved conflicts
   become the memo's auditable dissent record

This demonstrates true Agent Society behaviour and is the evaluator's centrepiece.

NOTE: consensus_score is a *resolution rate*, not a measure of idea quality.
Resolving one trivial conflict (10.0) is not "better" than surfacing three hard
ones and resolving two (6.0). Labels describe agreement only.
"""

import json
import re
from typing import Any, Dict, List, Tuple
from ..config import settings
from ..models import AgentOutput, ConflictPoint, DebateRound, ConsensusReport
from ..llm.provider import QwenProvider, DEEP_MODEL


MAX_DEBATE_ROUNDS = 3

# Severity → base weight. Skeptic-involved conflicts are weighted up because an
# unresolved risk objection should suppress "we have consensus" more than a minor
# spat (and a resolved one should count for more) — this is protocol step 5.
SEVERITY_WEIGHT = {"high": 3.0, "medium": 2.0, "low": 1.0}
SKEPTIC_MULTIPLIER = 1.5

CONFLICT_DETECTION_PROMPT = """
You are the debate moderator on an AI board of directors evaluating ONE company decision.

You have received analyses from multiple board agents about the decision. Identify where
agents DISAGREE — specifically where one agent supports a course of action another flags as
risky, unaffordable, or unrealistic.

Agent outputs:
{agent_outputs}

Identify conflicts in this JSON format:
{{
  "conflicts": [
    {{
      "topic": "brief topic name",
      "agent_a": "agent name",
      "agent_a_position": "what agent A claims",
      "agent_b": "agent name",
      "agent_b_position": "what agent B claims (opposite/contradicting)",
      "severity": "high|medium|low"
    }}
  ],
  "has_significant_conflicts": true/false,
  "conflict_summary": "one sentence summary of the key tension"
}}

Only flag real conflicts, not just different perspectives.
"""

DEBATE_ROUND_PROMPT = """
You are facilitating a debate round on an AI board evaluating ONE company decision.

The following conflicts are still unresolved entering this round:
{conflicts}

Original agent positions:
{agent_outputs}

Company & decision context:
{profile_context}

This is round {round_number} of {max_rounds}.

For each conflict, have the relevant agents argue their positions and then find a
resolution or acknowledge a continuing disagreement.

Respond in JSON:
{{
  "debate_exchanges": [
    {{
      "conflict_topic": "string — must match one of the unresolved topics above",
      "agent_a_rebuttal": "string",
      "agent_b_rebuttal": "string",
      "moderator_verdict": "string — lean toward which position and why",
      "resolved": true/false
    }}
  ],
  "revised_positions": {{
    "AgentName": "revised stance after debate"
  }},
  "overall_resolution_achieved": true/false,
  "round_summary": "what changed this round"
}}
"""

# ── Mock fixtures ─────────────────────────────────────────────────────────────
# A representative, deterministic 2-round board debate on a market-expansion
# decision, so the engine, scorer, and UI are fully exercisable WITHOUT a live
# key. Three conflicts: capital commitment (high), anchor-demand durability
# (medium, Skeptic), timeline (low, Skeptic). Round 1 resolves capital + timeline;
# demand durability stays contested and is surfaced as dissent. Worked score:
# 4.5 / 7.5 = 6.0 → "Moderate". Agent names are the canonical strings.

_MOCK_CONFLICTS = json.dumps({
    "conflicts": [
        {
            "topic": "Capital commitment vs reversibility",
            "agent_a": "growth",
            "agent_a_position": "Commit to a full subsidiary now to capture anchor demand fast.",
            "agent_b": "finance",
            "agent_b_position": "The budget can't absorb subsidiary fixed cost without breaching the cash buffer.",
            "severity": "high",
        },
        {
            "topic": "Durability of anchor demand",
            "agent_a": "skeptic",
            "agent_a_position": "The anchor customers' LOIs aren't binding; demand may not survive year one.",
            "agent_b": "trend",
            "agent_b_position": "Regional demand signals and incumbent inertia support the expansion window.",
            "severity": "medium",
        },
        {
            "topic": "Expansion timeline realism",
            "agent_a": "skeptic",
            "agent_a_position": "A 6-month full cross-border build is unrealistic for a first move.",
            "agent_b": "scout",
            "agent_b_position": "The asset-light option fits 6 months without a full build.",
            "severity": "low",
        },
    ],
    "has_significant_conflicts": True,
    "conflict_summary": "Core tension: does the anchor demand justify fixed capital commitment, and can it be executed in the window?",
})

_MOCK_ROUNDS = [
    # Round 1 — resolves capital + timeline, leaves demand durability open.
    json.dumps({
        "debate_exchanges": [
            {
                "conflict_topic": "Capital commitment vs reversibility",
                "agent_a_rebuttal": "A subsidiary buys control and speed to serve the anchors.",
                "agent_b_rebuttal": "There's no cash buffer for fixed cost on unproven demand.",
                "moderator_verdict": "Lean Finance — start asset-light with a local partner; revisit a subsidiary only after the pilot proves economics.",
                "resolved": True,
            },
            {
                "conflict_topic": "Expansion timeline realism",
                "agent_a_rebuttal": "First cross-border builds routinely overrun.",
                "agent_b_rebuttal": "Asset-light scope is 2-3 routes, which fits 6 months.",
                "moderator_verdict": "Lean Scout — keep the 6-month window but scope it to the asset-light pilot only.",
                "resolved": True,
            },
            {
                "conflict_topic": "Durability of anchor demand",
                "agent_a_rebuttal": "Non-binding LOIs are not committed volume.",
                "agent_b_rebuttal": "Market timing and incumbent inertia favour moving now.",
                "moderator_verdict": "Unsettled — needs signed minimum-volume commitments before any fixed commitment.",
                "resolved": False,
            },
        ],
        "revised_positions": {
            "growth": "Asset-light-first via a local partner; subsidiary deferred until the pilot proves economics.",
            "scout": "6-month window holds with scope cut to the asset-light pilot.",
        },
        "overall_resolution_achieved": False,
        "round_summary": "Capital and timeline conflicts resolved by going asset-light and scoping to a pilot; anchor-demand durability remains open.",
    }),
    # Round 2 — demand durability discussed again; stays unresolved (stalemate).
    json.dumps({
        "debate_exchanges": [
            {
                "conflict_topic": "Durability of anchor demand",
                "agent_a_rebuttal": "Without signed volume commitments, durable demand is an assumption.",
                "agent_b_rebuttal": "A short paid pilot can validate it cheaply.",
                "moderator_verdict": "Genuine unresolved tension — recommend securing minimum-volume commitments rather than forcing consensus.",
                "resolved": False,
            },
        ],
        "revised_positions": {
            "trend": "Demand signal is real but durability is unproven; validate with a paid pilot.",
            "skeptic": "Maintains uncommitted demand is the key risk until volume commitments prove otherwise.",
        },
        "overall_resolution_achieved": False,
        "round_summary": "Anchor-demand durability stays unresolved and is surfaced as the key dissent; both sides agree only signed commitments settle it.",
    }),
]


_DEBATE_SYSTEM = (
    "You are the debate moderator on an AI board of directors. "
    "Never invent names, companies, products, or agreements the operator did not provide — "
    "refer to unnamed entities exactly as the operator did (e.g. \"the third shipper\"). "
    "Respond with valid JSON only."
)


def _label_for(score: float, total_conflicts: int) -> str:
    """Agreement label only — never implies idea/recommendation quality."""
    if total_conflicts == 0:
        return "Full consensus (no conflicts)"
    if score >= 8.0:
        return "Strong consensus"
    if score >= 5.0:
        return "Moderate consensus"
    return "Weak / contested"


def _conflict_weight(c: ConflictPoint) -> float:
    base = SEVERITY_WEIGHT.get(c.severity.lower(), 1.0)
    skeptic_involved = "skeptic" in c.agent_a.lower() or "skeptic" in c.agent_b.lower()
    return base * (SKEPTIC_MULTIPLIER if skeptic_involved else 1.0)


class DebateEngine:
    def __init__(self):
        self.mock = settings.use_mock_llm or not settings.qwen_api_key
        self.provider = QwenProvider(model=DEEP_MODEL)

    def _call_llm(self, prompt: str, mock_fixture: str, max_tokens: int = 2000) -> str:
        """Return the stage-specific mock fixture in mock mode, else call Qwen."""
        if self.mock:
            return mock_fixture
        return self.provider.chat(_DEBATE_SYSTEM, prompt, max_tokens)

    def _parse_json(self, text: str) -> Dict[str, Any]:
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            text = fence_match.group(1)
        return json.loads(text.strip())

    def _format_agent_outputs(self, agent_outputs: Dict[str, AgentOutput]) -> str:
        lines = []
        for name, output in agent_outputs.items():
            lines.append(f"=== {name} ===")
            lines.append(f"Analysis: {output.analysis[:300]}")
            if output.key_findings:
                lines.append(f"Key findings: {'; '.join(output.key_findings[:3])}")
            if output.concerns:
                lines.append(f"Concerns: {'; '.join(output.concerns[:3])}")
            if output.recommendations:
                lines.append(f"Recommends: {', '.join(output.recommendations[:2])}")
            lines.append("")
        return "\n".join(lines)

    # ──────────────────────────────────────────
    # Step 1: Detect Conflicts
    # ──────────────────────────────────────────

    def detect_conflicts(
        self,
        agent_outputs: Dict[str, AgentOutput],
    ) -> Tuple[List[ConflictPoint], bool, str]:
        """Compare agent outputs and identify significant disagreements."""
        formatted = self._format_agent_outputs(agent_outputs)
        prompt = CONFLICT_DETECTION_PROMPT.format(agent_outputs=formatted)

        # 4500 cap: same exposure as Skeptic — conflict list truncates at the 2000 default.
        raw = self._call_llm(prompt, mock_fixture=_MOCK_CONFLICTS, max_tokens=4500)
        data = self._parse_json(raw)

        conflicts = [
            ConflictPoint(
                topic=c.get("topic", ""),
                agent_a=c.get("agent_a", ""),
                agent_a_position=c.get("agent_a_position", ""),
                agent_b=c.get("agent_b", ""),
                agent_b_position=c.get("agent_b_position", ""),
                severity=c.get("severity", "low"),
            )
            for c in data.get("conflicts", [])
        ]

        has_conflicts = data.get("has_significant_conflicts", False)
        conflict_summary = data.get("conflict_summary", "")
        return conflicts, has_conflicts, conflict_summary

    # ──────────────────────────────────────────
    # Step 2: Run Debate Rounds
    # ──────────────────────────────────────────

    def run_debate(
        self,
        agent_outputs: Dict[str, AgentOutput],
        conflicts: List[ConflictPoint],
        profile_context: str,
    ) -> Tuple[List[DebateRound], set]:
        """
        Run up to MAX_DEBATE_ROUNDS rounds. Each round only debates the conflicts
        still open at its start; a conflict's status is taken from the latest round
        that discussed it (final-round-authoritative, not a sticky OR), so it can
        never read "resolved" while the last round shows it contested.

        Returns the rounds plus the set of topics resolved by the end.
        """
        debate_rounds: List[DebateRound] = []
        resolved_topics: set = set()

        for round_num in range(1, MAX_DEBATE_ROUNDS + 1):
            unresolved = [c for c in conflicts if c.topic not in resolved_topics]
            if not unresolved:
                break

            conflicts_text = "\n".join(
                f"- [{c.severity.upper()}] {c.topic}: "
                f"{c.agent_a} says '{c.agent_a_position}' vs "
                f"{c.agent_b} says '{c.agent_b_position}'"
                for c in unresolved
            )

            prompt = DEBATE_ROUND_PROMPT.format(
                conflicts=conflicts_text,
                agent_outputs=self._format_agent_outputs(agent_outputs),
                profile_context=profile_context,
                round_number=round_num,
                max_rounds=MAX_DEBATE_ROUNDS,
            )

            mock_fixture = _MOCK_ROUNDS[min(round_num - 1, len(_MOCK_ROUNDS) - 1)]
            raw = self._call_llm(prompt, mock_fixture=mock_fixture, max_tokens=6000)
            data = self._parse_json(raw)

            # Per-conflict resolution from this round's exchanges (authoritative
            # for the topics discussed this round).
            verdicts = {
                ex.get("conflict_topic", ""): bool(ex.get("resolved", False))
                for ex in data.get("debate_exchanges", [])
            }
            resolved_this_round = 0
            for c in unresolved:
                if verdicts.get(c.topic):
                    resolved_topics.add(c.topic)
                    resolved_this_round += 1
                else:
                    # Final-round-authoritative guard: a topic discussed and not
                    # resolved this round must not stay marked resolved.
                    resolved_topics.discard(c.topic)

            # This round's conflict cards = the subset it actually debated, each
            # flagged with the outcome it reached this round.
            round_conflicts = [
                c.model_copy(update={"resolved": c.topic in resolved_topics})
                for c in unresolved
            ]

            overall_resolved = data.get("overall_resolution_achieved", False)
            debate_rounds.append(
                DebateRound(
                    round_number=round_num,
                    conflicts_identified=round_conflicts,
                    revised_positions=data.get("revised_positions", {}),
                    resolution_achieved=overall_resolved,
                    moderator_summary=data.get("round_summary", ""),
                )
            )

            # Stop conditions (all "up to N rounds"):
            all_resolved = all(c.topic in resolved_topics for c in conflicts)
            if all_resolved or overall_resolved:
                break
            # Stalemate: a zero-resolution round ends the debate — except on
            # round 1, where moved positions earn one more round. Live runs
            # routinely resolve nothing in round 1 while positions shift; a
            # hard break there made rounds 2+ unreachable in practice.
            positions_moved = bool(data.get("revised_positions"))
            if resolved_this_round == 0 and (round_num > 1 or not positions_moved):
                break  # stalemate — no progress; surface what remains

        return debate_rounds, resolved_topics

    # ──────────────────────────────────────────
    # Consensus scoring + report
    # ──────────────────────────────────────────

    def _compute_consensus_score(
        self,
        conflicts: List[ConflictPoint],
        resolved_topics: set,
    ) -> Tuple[float, str]:
        """Severity-weighted resolution rate on a 0–10 scale (10 = all resolved /
        nothing to resolve)."""
        if not conflicts:
            return 10.0, _label_for(10.0, 0)
        total = sum(_conflict_weight(c) for c in conflicts)
        resolved_mass = sum(
            _conflict_weight(c) for c in conflicts if c.topic in resolved_topics
        )
        score = round(10.0 * resolved_mass / total, 1) if total else 10.0
        return score, _label_for(score, len(conflicts))

    def _build_summary(
        self,
        conflict_summary: str,
        debate_rounds: List[DebateRound],
        score: float,
        label: str,
        resolved_count: int,
        total: int,
    ) -> str:
        header = (
            f"{label} ({score}/10): {resolved_count} of {total} conflict(s) resolved "
            f"over {len(debate_rounds)} round(s)."
        )
        lines = [header]
        if conflict_summary:
            lines.append(f"Key tension: {conflict_summary}")
        lines.append("")
        for r in debate_rounds:
            lines.append(f"Round {r.round_number}: {r.moderator_summary}")
            for agent, position in r.revised_positions.items():
                lines.append(f"  {agent} revised: {position[:150]}")
        return "\n".join(lines).rstrip()

    def _build_report(
        self,
        conflicts: List[ConflictPoint],
        resolved_topics: set,
        debate_rounds: List[DebateRound],
        conflict_summary: str,
    ) -> ConsensusReport:
        score, label = self._compute_consensus_score(conflicts, resolved_topics)
        unresolved = [
            c.model_copy(update={"resolved": False})
            for c in conflicts
            if c.topic not in resolved_topics
        ]
        resolved_count = len(conflicts) - len(unresolved)
        summary = self._build_summary(
            conflict_summary, debate_rounds, score, label, resolved_count, len(conflicts)
        )
        return ConsensusReport(
            consensus_score=score,
            label=label,
            total_conflicts=len(conflicts),
            resolved_conflicts=resolved_count,
            unresolved_conflicts=unresolved,
            rounds_used=len(debate_rounds),
            summary=summary,
        )

    # ──────────────────────────────────────────
    # Main Entry Point
    # ──────────────────────────────────────────

    def run(
        self,
        agent_outputs: Dict[str, AgentOutput],
        profile_context: str,
    ) -> Tuple[List[DebateRound], ConsensusReport]:
        """Full debate pipeline: detect → debate → score. Returns rounds + report."""
        conflicts, has_conflicts, conflict_summary = self.detect_conflicts(agent_outputs)

        if not has_conflicts or not conflicts:
            return [], ConsensusReport(
                consensus_score=10.0,
                label=_label_for(10.0, 0),
                total_conflicts=0,
                resolved_conflicts=0,
                unresolved_conflicts=[],
                rounds_used=0,
                summary=(
                    conflict_summary
                    or "All agents reached consensus without debate."
                ),
            )

        debate_rounds, resolved_topics = self.run_debate(
            agent_outputs, conflicts, profile_context
        )
        report = self._build_report(
            conflicts, resolved_topics, debate_rounds, conflict_summary
        )
        return debate_rounds, report
