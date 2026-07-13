"""
Feedback Intelligence Council — Track 3: Agent Society

A three-agent mini-council that reads user feedback from the vault and produces a ranked
product brief. Demonstrates:
  - Task decomposition: Analyst (cluster) → Skeptic (challenge) → Chair (synthesise)
  - Agent dialogue: each turn is recorded in council_dialogue for full auditability
  - Conflict resolution: Chair explicitly accepts, reframes, or overrides Skeptic challenges
  - Measurable efficiency gain: baseline (single-agent flat summary) vs. council output,
    with corrections_count as the integer delta

Run via POST /api/council-brief — completely separate from the main 8-agent pipeline.
"""

from __future__ import annotations

from typing import List

from ..agents.feedback_analyst import FeedbackAnalystAgent
from ..agents.feedback_skeptic import FeedbackSkepticAgent
from ..agents.feedback_chair import FeedbackChairAgent
from ..models import (
    CompanyProfile,
    FeedbackNote,
    FeedbackTheme,
    CouncilTurn,
    BaselineComparison,
    CouncilBriefResponse,
)

# Dummy profile — feedback agents ignore the company profile field; the council
# operates on vault feedback notes, not company-decision context.
_DUMMY_PROFILE = CompanyProfile(
    company_name="feedback-council",
    sector="internal",
    stage="",
    business_model="",
    size_band="",
)


class FeedbackCouncil:
    """
    Orchestrates the three-agent Feedback Intelligence Council.

    Execution order:
        1. FeedbackAnalystAgent  — clusters feedback into themes + baseline summary
        2. FeedbackSkepticAgent  — challenges the analyst's ranking
        3. FeedbackChairAgent    — synthesises into final brief, resolving each challenge
    """

    def run(self, feedback_notes: List[FeedbackNote], mock: bool = True) -> CouncilBriefResponse:
        texts = [n.text for n in feedback_notes]

        # ── 1. Analyst ────────────────────────────────────────────────────────
        analyst = FeedbackAnalystAgent()
        analyst.mock = mock
        analyst_out = analyst.analyze(_DUMMY_PROFILE, {"feedback_texts": texts})

        analyst_themes: List[dict] = analyst_out.raw_data.get("themes", [])
        baseline_summary: str = analyst_out.raw_data.get("baseline_summary", analyst_out.analysis)

        # ── 2. Skeptic ────────────────────────────────────────────────────────
        skeptic = FeedbackSkepticAgent()
        skeptic.mock = mock
        skeptic_out = skeptic.analyze(_DUMMY_PROFILE, {"analyst_themes": analyst_themes})

        challenges: List[dict] = skeptic_out.raw_data.get("challenges", [])
        accepted_themes: List[str] = skeptic_out.raw_data.get("accepted_themes", [])

        # ── 3. Chair ─────────────────────────────────────────────────────────
        chair = FeedbackChairAgent()
        chair.mock = mock
        chair_out = chair.analyze(_DUMMY_PROFILE, {
            "analyst_themes": analyst_themes,
            "skeptic_challenges": challenges,
            "accepted_themes": accepted_themes,
        })

        final_themes_raw: List[dict] = chair_out.raw_data.get("final_themes", [])
        overrides: List[dict] = chair_out.raw_data.get("overrides", [])
        ranked_brief: str = chair_out.raw_data.get("ranked_brief", chair_out.analysis)

        # ── Build council dialogue (the auditable exchange) ───────────────────
        council_dialogue = [
            CouncilTurn(
                agent=analyst.name,
                message=baseline_summary,
                challenges=[],
            ),
            CouncilTurn(
                agent=skeptic.name,
                message=analyst_out.analysis if not challenges else (
                    f"Raised {len(challenges)} challenge(s). "
                    + " | ".join(c["theme"] for c in challenges)
                ),
                challenges=[c["objection"] for c in challenges],
            ),
            CouncilTurn(
                agent=chair.name,
                message=ranked_brief,
                challenges=[],
            ),
        ]

        # ── Build final themes ────────────────────────────────────────────────
        final_themes = [
            FeedbackTheme(
                theme=t.get("theme", ""),
                frequency=t.get("frequency", 1),
                representative_quotes=t.get("representative_quotes", []),
                priority=t.get("priority", "medium"),
                thesis_aligned=t.get("thesis_aligned", True),
            )
            for t in final_themes_raw
        ]

        # ── Baseline comparison — what the council caught that one agent missed ─
        council_corrections = _derive_corrections(challenges, overrides)

        baseline_comparison = BaselineComparison(
            single_agent_summary=baseline_summary,
            council_corrections=council_corrections,
            corrections_count=len(council_corrections),
        )

        return CouncilBriefResponse(
            company_id="",          # filled in by the API route
            feedback_notes_read=len(feedback_notes),
            council_dialogue=council_dialogue,
            themes=final_themes,
            baseline_comparison=baseline_comparison,
            ranked_brief=ranked_brief,
            mock_mode=mock,
        )


def _derive_corrections(challenges: List[dict], overrides: List[dict]) -> List[str]:
    """
    Produce the list of things the council caught that a single agent would have missed.

    A "correction" is any challenge the Skeptic raised that the Chair acted on
    (accepted or reframed). Overridden challenges are not counted — the council
    ultimately agreed with the Analyst there.
    """
    override_by_theme = {o["theme"]: o for o in overrides}
    corrections: List[str] = []
    for c in challenges:
        override = override_by_theme.get(c["theme"])
        if override is None:
            continue
        decision = override.get("decision", "")
        if decision == "accepted":
            corrections.append(
                f"Removed '{c['theme']}' — {c['objection']}"
            )
        elif decision == "reframed":
            corrections.append(
                f"Reframed '{c['theme']}' — {override.get('rationale', c['objection'])}"
            )
    return corrections
