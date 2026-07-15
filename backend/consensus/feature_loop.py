"""
Feature Delivery Loop — SWE ⇄ QA iteration (Track 3: Agent Society).

Extends the Feedback Intelligence Council past "ranked brief" into delivery:

    signal gate (analyst) → Senior SWE builds a spec → QA reviews →
    fail? SWE revises → QA re-reviews (the loop) → pass? release to the vault

This adds the mechanic the council itself lacks — genuine ITERATION. Every turn
is recorded in loop_dialogue; every QA pass is a QARound; releases write a
`type: release` note to the company vault (excluded from decision retrieval).

Run via POST /api/feature-loop with a theme picked from the council's brief.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

from ..agents.swe import SeniorSWEAgent
from ..agents.qa import QAEngineerAgent
from ..config import settings
from ..models import (
    AgentOutput,
    BuildSpec,
    CompanyProfile,
    CouncilTurn,
    FeatureLoopResponse,
    FeedbackTheme,
    QAIssue,
    QARound,
    SignalGate,
)
from .. import vault

logger = logging.getLogger(__name__)

# QA review passes per run (1 initial + fixes). Env-tunable: live latency is
# ~2 deep calls per extra round, so the default stays tight.
MAX_QA_ROUNDS = int(os.environ.get("QA_LOOP_ROUNDS", "2"))

# The loop agents ignore company financials — the theme is the work item.
_DUMMY_PROFILE = CompanyProfile(
    company_name="delivery-loop",
    sector="internal",
    stage="",
    business_model="",
    size_band="",
)

_GATE_SYSTEM = (
    "You are the Data Analyst gate on a product-delivery loop. Given one feedback theme "
    "(with its frequency) and the total number of feedback notes read, decide whether the "
    "signal is strong enough to represent the needs of the majority of our users and target "
    "users — not one loud voice. Themes that are off-mandate (thesis_aligned=false) never "
    "pass. Return valid JSON only: {\"sufficient\": true/false, \"rationale\": \"one or two "
    "sentences\"}"
)


def _fallback_gate(theme: FeedbackTheme) -> SignalGate:
    """Deterministic gate for mock mode and any live-gate failure."""
    if not theme.thesis_aligned:
        return SignalGate(
            sufficient=False,
            rationale=(
                f"'{theme.theme}' is outside the product's mandate — building it would be "
                "scope creep regardless of how often it is asked for."
            ),
        )
    if theme.frequency >= 2:
        return SignalGate(
            sufficient=True,
            rationale=(
                f"{theme.frequency} independent reports of '{theme.theme}' — a recurring need "
                "across users, not a one-off. Enough signal to build against."
            ),
        )
    return SignalGate(
        sufficient=False,
        rationale=(
            f"Only {theme.frequency} report of '{theme.theme}' — one voice is not the "
            "majority of our users. Keep gathering feedback before committing build effort."
        ),
    )


class FeatureLoop:
    """Orchestrates one delivery-loop run for a council theme."""

    def run(
        self,
        company_id: str,
        theme: FeedbackTheme,
        feedback_notes_read: int = 0,
    ) -> FeatureLoopResponse:
        dialogue: List[CouncilTurn] = []
        mock = settings.use_mock_llm or not settings.qwen_api_key

        # ── 1. Signal gate (the Data Analyst's go/no-go) ─────────────────────
        gate = self._signal_gate(theme, feedback_notes_read, mock)
        dialogue.append(CouncilTurn(agent="feedback_analyst", message=gate.rationale))

        if not gate.sufficient:
            return FeatureLoopResponse(
                company_id=company_id,
                theme=theme,
                gate=gate,
                loop_dialogue=dialogue,
                status="insufficient_signal",
                mock_mode=mock,
            )

        # ── 2/3/4. SWE builds → QA reviews → SWE fixes → QA re-reviews ──────
        # One agent instance each across the whole loop: the mock fixtures are
        # call-counted, and a live SWE revision needs its own prior context.
        swe = SeniorSWEAgent()
        qa = QAEngineerAgent()

        spec_raw: Dict[str, Any] = {}
        qa_rounds: List[QARound] = []
        released = False

        for round_no in range(1, MAX_QA_ROUNDS + 1):
            # SWE: build on round 1, revise on later rounds using QA's issues.
            swe_ctx: Dict[str, Any] = {"theme": theme.model_dump()}
            if spec_raw:
                swe_ctx["previous_spec"] = spec_raw
                swe_ctx["qa_issues"] = [i.model_dump() for i in qa_rounds[-1].issues]
            try:
                swe_out = swe.analyze(_DUMMY_PROFILE, swe_ctx)
            except Exception as exc:
                logger.warning("SeniorSWEAgent failed on round %d: %s", round_no, exc)
                swe_out = AgentOutput(
                    agent_name=swe.name, role=swe.role,
                    analysis="SWE unavailable.", raw_data={},
                )
            spec_raw = swe_out.raw_data or spec_raw
            dialogue.append(CouncilTurn(
                agent=swe.name,
                message=(
                    f"{'Revised spec' if round_no > 1 else 'Build spec'}: "
                    f"{swe_out.analysis or spec_raw.get('feature_name', '(no spec)')}"
                ),
            ))

            # QA: review the current spec.
            try:
                qa_out = qa.analyze(_DUMMY_PROFILE, {"spec": spec_raw, "round": round_no})
                qa_data = qa_out.raw_data
            except Exception as exc:
                logger.warning("QAEngineerAgent failed on round %d: %s", round_no, exc)
                qa_out = AgentOutput(
                    agent_name=qa.name, role=qa.role,
                    analysis="QA unavailable — release blocked.", raw_data={},
                )
                # A QA failure must never ship a feature: treat as a failing round.
                qa_data = {"verdict": "fail", "issues": [{
                    "severity": "high", "category": "gap",
                    "description": "QA review could not run — release blocked.",
                    "location": "loop",
                }]}

            issues = [
                QAIssue(**i) for i in qa_data.get("issues", []) if isinstance(i, dict)
            ]
            verdict = "pass" if qa_data.get("verdict") == "pass" else "fail"
            qa_rounds.append(QARound(round=round_no, verdict=verdict, issues=issues))
            dialogue.append(CouncilTurn(
                agent=qa.name,
                message=qa_out.analysis or f"Round {round_no}: {verdict}.",
                challenges=[i.description for i in issues],
            ))

            if verdict == "pass":
                released = True
                break

        build_spec = BuildSpec(**spec_raw) if spec_raw.get("feature_name") else None

        # ── 5. Release (vault write) or hold at the cap ──────────────────────
        release_path = ""
        if released and build_spec is not None:
            try:
                release_path = vault.write_release(company_id, build_spec, theme.theme)
            except Exception:
                logger.exception("Release note write failed for %s", company_id)

        return FeatureLoopResponse(
            company_id=company_id,
            theme=theme,
            gate=gate,
            loop_dialogue=dialogue,
            build_spec=build_spec,
            qa_rounds=qa_rounds,
            iterations=len(qa_rounds),
            status="released" if released else "held",
            release_note_path=release_path,
            mock_mode=mock,
        )

    def _signal_gate(
        self, theme: FeedbackTheme, feedback_notes_read: int, mock: bool
    ) -> SignalGate:
        """Live: one FAST_MODEL call. Mock or any failure: the deterministic rule."""
        if mock:
            return _fallback_gate(theme)
        try:
            from ..llm.provider import QwenProvider, FAST_MODEL

            user = (
                f"Theme under consideration:\n{json.dumps(theme.model_dump(), indent=2)}\n\n"
                f"Total feedback notes read: {feedback_notes_read}"
            )
            raw = QwenProvider(model=FAST_MODEL).chat(_GATE_SYSTEM, user, max_tokens=300)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            data = json.loads(m.group()) if m else {}
            return SignalGate(
                sufficient=bool(data.get("sufficient", False)),
                rationale=str(data.get("rationale", "")) or _fallback_gate(theme).rationale,
            )
        except Exception:
            logger.warning("Live signal gate failed — falling back to the deterministic rule")
            return _fallback_gate(theme)
