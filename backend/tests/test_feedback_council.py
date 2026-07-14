"""
Tests for the Feedback Intelligence Council — Track 3: Agent Society.

All tests are hermetic (mock-pinned via conftest.py) and offline. They verify:
  - The council produces a valid CouncilBriefResponse
  - All three agent turns appear in council_dialogue (the auditable exchange)
  - The baseline comparison is present and non-trivial (council caught something)
  - The Chair resolves the Skeptic's challenges (themes change post-debate)
  - Mock mode propagates correctly
"""

import pytest
from backend.consensus.feedback_council import FeedbackCouncil
from backend.models import FeedbackNote, CouncilBriefResponse


@pytest.fixture
def sample_notes():
    return [
        FeedbackNote(
            text="The board didn't factor in port congestion risk at Cai Mep.",
            date="2026-07-09",
            response_id="fb001",
        ),
        FeedbackNote(
            text="Customs brokerage timeline was listed as a missing input but should have been flagged as a blocker.",
            date="2026-07-09",
            response_id="fb002",
        ),
        FeedbackNote(
            text="Board should have recommended a logistics software like project44 or Flexport.",
            date="2026-07-09",
            response_id="fb003",
        ),
    ]


@pytest.fixture
def council_response(sample_notes):
    council = FeedbackCouncil()
    return council.run(sample_notes, company_id="harborline-logistics")


def test_council_returns_valid_response(council_response):
    assert isinstance(council_response, CouncilBriefResponse)
    assert council_response.company_id == "harborline-logistics"
    assert council_response.feedback_notes_read == 3
    assert council_response.ranked_brief
    assert isinstance(council_response.mock_mode, bool)
    assert council_response.mock_mode is True


def test_three_agent_dialogue_visible(council_response):
    dialogue = council_response.council_dialogue
    assert len(dialogue) == 3
    agents = [turn.agent for turn in dialogue]
    assert "feedback_analyst" in agents
    assert "feedback_skeptic" in agents
    assert "feedback_chair" in agents


def test_each_dialogue_turn_has_message(council_response):
    for turn in council_response.council_dialogue:
        assert turn.message, f"Agent {turn.agent} has empty message"


def test_skeptic_raises_at_least_one_challenge(council_response):
    skeptic_turn = next(
        t for t in council_response.council_dialogue if t.agent == "feedback_skeptic"
    )
    assert len(skeptic_turn.challenges) >= 1, "Skeptic should raise at least one challenge"


def test_baseline_comparison_present(council_response):
    bc = council_response.baseline_comparison
    assert bc.single_agent_summary
    assert bc.corrections_count >= 1, (
        "Council should catch at least one thing the single agent missed"
    )
    assert len(bc.council_corrections) == bc.corrections_count


def test_themes_change_after_debate(council_response):
    # The Chair should produce fewer or differently-named themes than the Analyst's raw output
    # (the software-recommendation theme should be reframed/removed)
    theme_names = [t.theme for t in council_response.themes]
    assert theme_names, "Chair must produce at least one final theme"
    # Original analyst theme should not survive verbatim after Skeptic challenged it
    assert "Software and vendor recommendations" not in theme_names, (
        "Thesis-misaligned theme should be reframed or removed by the Chair"
    )


def test_all_final_themes_are_thesis_aligned(council_response):
    for theme in council_response.themes:
        assert theme.thesis_aligned, (
            f"Theme '{theme.theme}' is not thesis-aligned — Chair should have reframed or removed it"
        )


def test_mock_mode_flag_propagated(council_response):
    assert council_response.mock_mode is True


def test_empty_feedback_returns_gracefully():
    council = FeedbackCouncil()
    resp = council.run([], company_id="harborline-logistics")
    assert isinstance(resp, CouncilBriefResponse)
    assert resp.feedback_notes_read == 0
