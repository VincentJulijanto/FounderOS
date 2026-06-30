"""
Debate Engine — the core innovation of FounderOS.

Instead of chaining agents linearly, this engine:
1. Collects all agent outputs
2. Detects disagreements between agents
3. Runs up to MAX_DEBATE_ROUNDS debate rounds where agents revise positions
4. Scores how much of the (severity-weighted) disagreement was resolved
5. Produces a ConsensusReport + summary for the Venture Partner

This demonstrates true Agent Society behaviour.

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
You are a debate moderator at an AI Venture Studio.

You have received analyses from multiple agents about startup opportunities.
Identify where agents DISAGREE — specifically where one agent recommends something
another agent flags as risky or infeasible.

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
      "severity": "high|medium|low",
      "opportunity_name": "which startup idea this concerns"
    }}
  ],
  "has_significant_conflicts": true/false,
  "conflict_summary": "one sentence summary of the key tension"
}}

Only flag real conflicts, not just different perspectives.
"""

DEBATE_ROUND_PROMPT = """
You are facilitating a debate round at an AI Venture Studio.

The following conflicts are still unresolved entering this round:
{conflicts}

Original agent positions:
{agent_outputs}

User's profile context:
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
# A representative, deterministic 2-round negotiation on the "AI Study Buddy"
# profile so the debate engine, scorer, and UI are fully exercisable WITHOUT a
# live key. Three conflicts: budget (high), willingness-to-pay (medium, Skeptic),
# timeline (low, Skeptic). Round 1 resolves budget + timeline; willingness-to-pay
# stays contested and is surfaced. Worked score: 4.5 / 7.5 = 6.0 → "Moderate".

_MOCK_CONFLICTS = json.dumps({
    "conflicts": [
        {
            "topic": "Paid acquisition vs zero ad budget",
            "agent_a": "Growth Agent",
            "agent_a_position": "Scale via paid TikTok ads to reach the first 100 users quickly.",
            "agent_b": "Finance Agent",
            "agent_b_position": "The SGD 300 budget supports effectively zero paid ad spend — organic only.",
            "severity": "high",
            "opportunity_name": "AI Study Buddy",
        },
        {
            "topic": "Willingness to pay",
            "agent_a": "Skeptic Agent",
            "agent_a_position": "Students won't pay SGD 9/mo when free AI tools already exist.",
            "agent_b": "Trend Analyst",
            "agent_b_position": "35% YoY edtech growth and exam-season urgency support paid conversion.",
            "severity": "medium",
            "opportunity_name": "AI Study Buddy",
        },
        {
            "topic": "Launch timeline realism",
            "agent_a": "Skeptic Agent",
            "agent_a_position": "A 3-week solo launch is unrealistic.",
            "agent_b": "Opportunity Scout",
            "agent_b_position": "The MVP scope is small enough to ship in 3 weeks.",
            "severity": "low",
            "opportunity_name": "AI Study Buddy",
        },
    ],
    "has_significant_conflicts": True,
    "conflict_summary": "Core tension: can a SGD 300, 3-week solo build convert price-sensitive students into paying users?",
})

_MOCK_ROUNDS = [
    # Round 1 — resolves budget + timeline, leaves willingness-to-pay open.
    json.dumps({
        "debate_exchanges": [
            {
                "conflict_topic": "Paid acquisition vs zero ad budget",
                "agent_a_rebuttal": "Paid ads buy speed to the first 100 users.",
                "agent_b_rebuttal": "There is no cash for paid; free campus channels exist.",
                "moderator_verdict": "Lean Finance — start organic (campus ambassadors, Reddit); revisit paid only after first revenue.",
                "resolved": True,
            },
            {
                "conflict_topic": "Launch timeline realism",
                "agent_a_rebuttal": "Solo founders routinely slip on timelines.",
                "agent_b_rebuttal": "Scope is note-upload + Q&A only; that fits 3 weeks.",
                "moderator_verdict": "Lean Scout — keep 3 weeks but cut scope to the single core flow.",
                "resolved": True,
            },
            {
                "conflict_topic": "Willingness to pay",
                "agent_a_rebuttal": "Free substitutes cap pricing power.",
                "agent_b_rebuttal": "Exam-time urgency drives willingness to pay.",
                "moderator_verdict": "Unsettled — needs a live pricing test before any commitment.",
                "resolved": False,
            },
        ],
        "revised_positions": {
            "Growth Agent": "Organic-first (campus ambassadors + Reddit); paid ads deferred until post-revenue.",
            "Opportunity Scout": "3-week launch holds with scope cut to note-upload + Q&A only.",
        },
        "overall_resolution_achieved": False,
        "round_summary": "Budget and timeline conflicts resolved by going organic-first and trimming MVP scope; willingness-to-pay remains open.",
    }),
    # Round 2 — willingness-to-pay discussed again; stays unresolved (stalemate).
    json.dumps({
        "debate_exchanges": [
            {
                "conflict_topic": "Willingness to pay",
                "agent_a_rebuttal": "Without a paywall test, paid conversion is an assumption.",
                "agent_b_rebuttal": "A freemium trial can validate it cheaply.",
                "moderator_verdict": "Genuine unresolved tension — recommend a freemium pricing experiment rather than forcing consensus.",
                "resolved": False,
            },
        ],
        "revised_positions": {
            "Trend Analyst": "Demand is real but pricing power is unproven; validate with a freemium test.",
            "Skeptic Agent": "Maintains paid conversion is the key risk until a pricing test proves otherwise.",
        },
        "overall_resolution_achieved": False,
        "round_summary": "Willingness-to-pay stays unresolved and is surfaced as the key risk; both sides agree only a live pricing test settles it.",
    }),
]


_DEBATE_SYSTEM = "You are a debate moderator at an AI Venture Studio. Respond with valid JSON only."


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
            raw = self._call_llm(prompt, mock_fixture=mock_fixture, max_tokens=2500)
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
            if resolved_this_round == 0:
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
