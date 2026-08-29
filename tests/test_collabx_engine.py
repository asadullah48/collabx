import pytest

from collabx.core.models import EditorialBrief, ResearchDossier, ToneStyle
from collabx.core.tone import profile_for
from collabx.orchestration.collabx_engine import CollabXEngine


def test_collabx_engine_end_to_end():
    engine = CollabXEngine()
    brief = EditorialBrief(topic="Enterprise Agent Workforces")
    pub = engine.produce_edition(brief)

    assert len(pub.research_dossier.findings) >= 2
    assert pub.title.startswith("The Next Frontier:")
    # A real Flesch score, not a constant: it must be in range and must clear
    # the floor for this brief's tone.
    floor = profile_for(brief.tone).readability_floor
    assert 0.0 <= pub.feedback.readability_score <= 100.0
    assert pub.feedback.readability_score >= floor


def test_readability_score_responds_to_the_brief_topic():
    # The score is computed from the draft, so a different topic -- which flows
    # into the headline -- must be able to move it. A constant cannot.
    engine = CollabXEngine()
    short = engine.produce_edition(EditorialBrief(topic="AI at Work"))
    long = engine.produce_edition(
        EditorialBrief(
            topic="Heterogeneous Orchestration Methodologies for Multinational "
            "Enterprise Infrastructure Modernization"
        )
    )
    assert short.feedback.readability_score != long.feedback.readability_score


def test_engine_is_deterministic_for_the_same_brief():
    brief = EditorialBrief(topic="Enterprise Agent Workforces")
    first = CollabXEngine().produce_edition(brief)
    second = CollabXEngine().produce_edition(brief)

    assert first.edition_id == second.edition_id
    assert first.final_markdown == second.final_markdown
    assert first.feedback.readability_score == second.feedback.readability_score


def test_revision_loop_runs_when_the_first_draft_misses_its_floor():
    # ENGAGING_STORYTELLER has the highest readability floor, and the first
    # draft lands just under it. With no budget the edition still publishes,
    # carrying a failing verdict; with a budget the loop fixes it.
    brief = EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER)
    floor = profile_for(ToneStyle.ENGAGING_STORYTELLER).readability_floor

    unrevised = CollabXEngine(max_revision_rounds=0).produce_edition(brief)
    revised = CollabXEngine(max_revision_rounds=2).produce_edition(brief)

    assert unrevised.feedback.readability_score < floor
    assert unrevised.feedback.revision_required is True
    assert revised.feedback.readability_score >= floor
    assert revised.feedback.revision_required is False
    assert revised.feedback.readability_score > unrevised.feedback.readability_score


def test_exhausted_budget_still_publishes_with_a_failing_verdict():
    # The endpoint stays total: a rejected draft is returned, not withheld.
    brief = EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER)
    pub = CollabXEngine(max_revision_rounds=0).produce_edition(brief)

    assert pub.final_markdown.strip()
    assert pub.html_body.strip()
    assert pub.feedback.revision_required is True
    failing = next(n for n in pub.feedback.critique_notes if "Failing gates" in n)
    assert "readability" in failing
    # The margin is reported, not just the fact of failure.
    assert any("Short by" in n for n in pub.feedback.critique_notes)


def test_exhausted_budget_does_not_claim_revision_was_unnecessary():
    pub = CollabXEngine(max_revision_rounds=0).produce_edition(
        EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER)
    )
    loop_note = next(n for n in pub.feedback.critique_notes if "Editorial loop" in n)
    assert "no revision needed" not in loop_note


def test_loop_terminates_even_with_a_large_budget():
    # The Writer is deterministic: once a round changes nothing, more rounds
    # cannot help. A generous budget must not mean a generous runtime.
    brief = EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER)
    pub = CollabXEngine(max_revision_rounds=500).produce_edition(brief)
    loop_note = next(n for n in pub.feedback.critique_notes if "Editorial loop" in n)
    assert "500" not in loop_note


def test_revision_preserves_grounding():
    # A revision that mangled a statistic would turn an improvement into a
    # regression, so the transforms must leave protected spans alone.
    brief = EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER)
    pub = CollabXEngine(max_revision_rounds=2).produce_edition(brief)
    assert pub.feedback.fact_check_passed is True


def test_brief_tone_changes_the_published_edition():
    # tone was previously read by nothing at all.
    pioneer = CollabXEngine().produce_edition(
        EditorialBrief(topic="Agent Workforces", tone=ToneStyle.TECH_PIONEER)
    )
    executive = CollabXEngine().produce_edition(
        EditorialBrief(topic="Agent Workforces", tone=ToneStyle.EXECUTIVE_BRIEF)
    )
    assert pioneer.title != executive.title
    assert pioneer.final_markdown != executive.final_markdown


def test_brief_target_word_count_changes_the_published_edition():
    # target_word_count was previously read by nothing at all.
    brief_short = EditorialBrief(topic="Agent Workforces", target_word_count=80)
    brief_long = EditorialBrief(topic="Agent Workforces", target_word_count=650)
    short = CollabXEngine().produce_edition(brief_short)
    long = CollabXEngine().produce_edition(brief_long)
    assert len(short.final_markdown) < len(long.final_markdown)
