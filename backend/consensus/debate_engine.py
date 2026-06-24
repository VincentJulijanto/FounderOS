"""
Debate Engine — the core innovation of FounderOS.

Instead of chaining agents linearly, this engine:
1. Collects all agent outputs
2. Detects disagreements between agents
3. Runs up to MAX_ROUNDS debate rounds where agents revise positions
4. Produces a consensus summary for the Venture Partner

This demonstrates true Agent Society behaviour.
"""

import json
import anthropic
from typing import Dict, Any
from ..config import settings
from ..models import AgentOutput, ConflictPoint, DebateRound


MAX_DEBATE_ROUNDS = 3

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

The following conflicts were identified between agents:
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
      "conflict_topic": "string",
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


class DebateEngine:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call_claude(self, prompt: str, max_tokens: int = 2000) -> str:
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse_json(self, text: str) -> Dict[str, Any]:
        import re
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
    ) -> tuple[list[ConflictPoint], bool]:
        """
        Compare agent outputs and identify significant disagreements.
        Returns (list of ConflictPoints, has_significant_conflicts).
        """
        formatted = self._format_agent_outputs(agent_outputs)
        prompt = CONFLICT_DETECTION_PROMPT.format(agent_outputs=formatted)

        raw = self._call_claude(prompt)
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
        return conflicts, has_conflicts

    # ──────────────────────────────────────────
    # Step 2: Run Debate Rounds
    # ──────────────────────────────────────────

    def run_debate(
        self,
        agent_outputs: Dict[str, AgentOutput],
        conflicts: list[ConflictPoint],
        profile_context: str,
    ) -> tuple[list[DebateRound], str]:
        """
        Run up to MAX_DEBATE_ROUNDS rounds of debate.
        Returns (list of DebateRounds, final consensus summary).
        """
        debate_rounds: list[DebateRound] = []
        current_positions = {
            name: output.analysis for name, output in agent_outputs.items()
        }
        resolution_achieved = False

        for round_num in range(1, MAX_DEBATE_ROUNDS + 1):
            conflicts_text = "\n".join(
                f"- [{c.severity.upper()}] {c.topic}: "
                f"{c.agent_a} says '{c.agent_a_position}' vs "
                f"{c.agent_b} says '{c.agent_b_position}'"
                for c in conflicts
            )

            prompt = DEBATE_ROUND_PROMPT.format(
                conflicts=conflicts_text,
                agent_outputs=self._format_agent_outputs(agent_outputs),
                profile_context=profile_context,
                round_number=round_num,
                max_rounds=MAX_DEBATE_ROUNDS,
            )

            raw = self._call_claude(prompt, max_tokens=2500)
            data = self._parse_json(raw)

            round_result = DebateRound(
                round_number=round_num,
                conflicts_identified=conflicts,
                revised_positions=data.get("revised_positions", {}),
                resolution_achieved=data.get("overall_resolution_achieved", False),
                moderator_summary=data.get("round_summary", ""),
            )
            debate_rounds.append(round_result)

            # Update running positions
            current_positions.update(data.get("revised_positions", {}))

            if data.get("overall_resolution_achieved", False):
                resolution_achieved = True
                break

        # Build consensus summary for Venture Partner
        consensus_summary = self._build_consensus_summary(debate_rounds, resolution_achieved)
        return debate_rounds, consensus_summary

    def _build_consensus_summary(
        self,
        rounds: list[DebateRound],
        resolution_achieved: bool,
    ) -> str:
        if not rounds:
            return "No debate was needed — agents were in agreement."

        lines = [
            f"Debate completed in {len(rounds)} round(s). "
            f"Resolution: {'ACHIEVED' if resolution_achieved else 'PARTIAL — some disagreements remain'}.",
            ""
        ]
        for r in rounds:
            lines.append(f"Round {r.round_number}: {r.moderator_summary}")
            for agent, position in r.revised_positions.items():
                lines.append(f"  {agent} revised: {position[:150]}")

        return "\n".join(lines)

    # ──────────────────────────────────────────
    # Main Entry Point
    # ──────────────────────────────────────────

    def run(
        self,
        agent_outputs: Dict[str, AgentOutput],
        profile_context: str,
    ) -> tuple[list[DebateRound], str]:
        """
        Full debate pipeline: detect conflicts → debate → return rounds + summary.
        """
        conflicts, has_conflicts = self.detect_conflicts(agent_outputs)

        if not has_conflicts or not conflicts:
            return [], "All agents reached consensus without debate."

        return self.run_debate(agent_outputs, conflicts, profile_context)
