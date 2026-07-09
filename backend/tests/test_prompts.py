"""Guard the anti-invention instruction in every board prompt (live-run finding #1:
the board named unnamed entities — invented client/partner companies — in a memo)."""

from backend.agents import scout, trend, finance, growth, skeptic, capability, venture_partner, research
from backend.consensus.debate_engine import _DEBATE_SYSTEM

ANTI_INVENTION = "Never invent names, companies, products, or agreements"


def test_every_agent_prompt_forbids_invented_names():
    for module in (scout, trend, finance, growth, skeptic, capability, venture_partner):
        assert ANTI_INVENTION in module.SYSTEM_PROMPT, module.__name__


def test_research_prompts_forbid_invented_names():
    # Research has two prompts (query generation + extraction); both must carry the guard.
    assert ANTI_INVENTION in research.SYSTEM_PROMPT_QUERIES
    assert ANTI_INVENTION in research.SYSTEM_PROMPT_EXTRACT


def test_debate_moderator_prompt_forbids_invented_names():
    assert ANTI_INVENTION in _DEBATE_SYSTEM
