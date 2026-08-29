import pytest

from collabx.agents.researcher_agent import ResearcherAgent
from collabx.agents.writer_agent import RevisionHint, WriterAgent
from collabx.core.grounding import check_grounding
from collabx.core.models import EditorialBrief, ToneStyle
from collabx.core.readability import flesch_reading_ease


@pytest.fixture
def researcher():
    return ResearcherAgent()


@pytest.fixture
def writer():
    return WriterAgent()


def test_writer_agent_composition(researcher, writer):
    brief = EditorialBrief(topic="Multi-Agent Systems")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)

    # One section per finding, plus the takeaway.
    assert len(draft.sections) == len(dossier.findings) + 1
    assert draft.word_count > 50
    assert draft.headline.startswith("The Next Frontier:")


def test_the_draft_is_built_from_the_dossier_not_from_fixed_text(researcher, writer):
    brief = EditorialBrief(topic="Multi-Agent Systems")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)

    # Every statistic must appear verbatim, or grounding has nothing to trace.
    for finding in dossier.findings:
        assert finding.statistic in draft.raw_markdown


def test_every_claim_in_a_fresh_draft_is_grounded(researcher, writer):
    brief = EditorialBrief(topic="Multi-Agent Systems")
    dossier = researcher.conduct_research(brief)
    report = check_grounding(writer.compose_draft(brief, dossier), dossier)
    assert report.passed is True
    assert report.checked_count > 0


def test_tone_changes_the_headline_and_the_body(researcher, writer):
    # brief.tone was previously read by nothing at all.
    brief_a = EditorialBrief(topic="Agent Systems", tone=ToneStyle.TECH_PIONEER)
    brief_b = EditorialBrief(topic="Agent Systems", tone=ToneStyle.EXECUTIVE_BRIEF)
    dossier = researcher.conduct_research(brief_a)

    a = writer.compose_draft(brief_a, dossier)
    b = writer.compose_draft(brief_b, dossier)

    assert a.headline != b.headline
    assert a.hook != b.hook
    assert a.raw_markdown != b.raw_markdown


@pytest.mark.parametrize("tone", list(ToneStyle))
def test_every_tone_produces_a_draft(researcher, writer, tone):
    # A missing entry in any per-tone table would be a KeyError at request time.
    brief = EditorialBrief(topic="Agent Systems", tone=tone)
    draft = writer.compose_draft(brief, researcher.conduct_research(brief))
    assert draft.raw_markdown.strip()
    assert draft.headline.endswith("Agent Systems")


def test_target_word_count_changes_the_length_of_the_draft(researcher, writer):
    # brief.target_word_count was previously read by nothing at all.
    brief_short = EditorialBrief(topic="Agent Systems", target_word_count=80)
    brief_long = EditorialBrief(topic="Agent Systems", target_word_count=650)
    dossier = researcher.conduct_research(brief_short)

    short = writer.compose_draft(brief_short, dossier)
    long = writer.compose_draft(brief_long, dossier)

    assert short.word_count < long.word_count


def test_sections_do_not_repeat_the_same_body_text(researcher, writer):
    brief = EditorialBrief(topic="Agent Systems")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)

    bodies = [section.content_markdown for section in draft.sections]
    assert len(bodies) == len(set(bodies))


def test_each_section_attributes_its_own_source(researcher, writer):
    brief = EditorialBrief(topic="Agent Systems")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)

    for finding, section in zip(dossier.findings, draft.sections):
        host = finding.source_url.split("//", 1)[-1].split("/", 1)[0]
        assert host in section.content_markdown


def test_a_revision_hint_produces_more_readable_output(researcher, writer):
    brief = EditorialBrief(topic="Agent Systems", tone=ToneStyle.ENGAGING_STORYTELLER)
    dossier = researcher.conduct_research(brief)

    base = writer.compose_draft(brief, dossier)
    revised = writer.compose_draft(
        brief,
        dossier,
        revision_hint=RevisionHint(max_sentence_words=12, simplify_vocabulary=True),
    )
    assert flesch_reading_ease(revised.raw_markdown) > flesch_reading_ease(
        base.raw_markdown
    )


def test_revision_does_not_break_grounding(researcher, writer):
    brief = EditorialBrief(topic="Agent Systems", tone=ToneStyle.ENGAGING_STORYTELLER)
    dossier = researcher.conduct_research(brief)
    revised = writer.compose_draft(
        brief,
        dossier,
        revision_hint=RevisionHint(max_sentence_words=10, simplify_vocabulary=True),
    )
    assert check_grounding(revised, dossier).passed is True


def test_composition_is_deterministic(researcher, writer):
    brief = EditorialBrief(topic="Agent Systems")
    dossier = researcher.conduct_research(brief)
    first = writer.compose_draft(brief, dossier)
    second = writer.compose_draft(brief, dossier)
    assert first.raw_markdown == second.raw_markdown
    assert first.draft_id == second.draft_id
