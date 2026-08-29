import pytest

from collabx.core.grounding import (
    check_grounding,
    extract_quotes,
    extract_statistics,
    topic_coherence_note,
    topic_terms,
)
from collabx.core.models import (
    ArticleDraft,
    NewsletterSection,
    ResearchDossier,
    ResearchFinding,
)


def _dossier() -> ResearchDossier:
    return ResearchDossier(
        dossier_id="DOS-1",
        topic="Enterprise AI",
        findings=[
            ResearchFinding(
                headline="Adoption climbs",
                statistic="61% of teams shipped an agent feature this year.",
                source_url="https://example.com/research",
                verified_quote="Adoption moved from pilots to production.",
            ),
            ResearchFinding(
                headline="Error rates fall",
                statistic="2.5x fewer production incidents after rollout.",
                source_url="https://example.com/incidents",
                verified_quote="The failure curve flattened within one quarter.",
            ),
        ],
        core_themes=["Enterprise AI adoption"],
    )


def _draft(markdown: str) -> ArticleDraft:
    return ArticleDraft(
        draft_id="D1",
        headline="H",
        subheadline="S",
        hook="Hook",
        sections=[NewsletterSection(heading="Sec", content_markdown=markdown)],
        raw_markdown=markdown,
        word_count=len(markdown.split()),
    )


# --- what counts as a checkable claim -------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Growth hit 61% last year.", ["61%"]),
        ("A 2.5x improvement.", ["2.5x"]),
        ("Revenue reached $4.2B overall.", ["$4.2B"]),
        ("About 3 million users joined.", ["3 million"]),
    ],
)
def test_numbers_with_a_unit_are_treated_as_claims(text, expected):
    assert extract_statistics(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "## 1. The Shift from Assist to Execute",   # heading ordinal
        "By 2026 the picture had changed.",          # a year
        "Fortune 500 teams reported the same.",      # part of a proper noun
    ],
)
def test_bare_integers_are_not_treated_as_claims(text):
    # A naive \d+ would flag all of these, failing every draft for typographic
    # reasons rather than for fabrication.
    assert extract_statistics(text) == []


def test_double_quoted_spans_are_extracted():
    assert extract_quotes('He said "the failure curve flattened" last week.') == [
        "the failure curve flattened"
    ]


def test_contractions_are_not_mistaken_for_quoted_spans():
    # A naive single-quote pattern reads "don't ... it's" as a quotation.
    assert extract_quotes("It don't matter what it's called around here.") == []


def test_single_quoted_spans_at_word_boundaries_are_extracted():
    assert extract_quotes("*'Adoption moved from pilots to production.'*") == [
        "Adoption moved from pilots to production."
    ]


# --- verification ----------------------------------------------------------


def test_statistics_present_in_the_dossier_are_supported():
    report = check_grounding(_draft("Growth hit 61% this year."), _dossier())
    assert report.passed is True
    assert report.supported_statistics == ["61%"]


def test_statistics_absent_from_the_dossier_are_reported_unsupported():
    report = check_grounding(_draft("Growth hit 94% this year."), _dossier())
    assert report.passed is False
    assert report.unsupported_statistics == ["94%"]
    assert any("94%" in note for note in report.notes())


def test_a_quote_is_grounded_with_or_without_its_trailing_period():
    with_stop = check_grounding(
        _draft('He said "Adoption moved from pilots to production." today.'), _dossier()
    )
    without_stop = check_grounding(
        _draft('He said "Adoption moved from pilots to production" today.'), _dossier()
    )
    assert with_stop.passed is True
    assert without_stop.passed is True


def test_an_invented_quote_fails_the_check():
    report = check_grounding(
        _draft('An analyst said "this number was never published anywhere".'), _dossier()
    )
    assert report.passed is False
    assert report.unsupported_quotes


def test_a_draft_with_no_checkable_claims_says_so_explicitly():
    # It reports passed, because there are no unsupported claims -- but the
    # note must not let a reader believe verification actually happened.
    report = check_grounding(_draft("The team shipped it. The work went well."), _dossier())
    assert report.checked_count == 0
    assert any("nothing could be verified" in note for note in report.notes())


def test_notes_report_how_many_claims_were_checked():
    report = check_grounding(_draft("Growth hit 61% and errors fell 2.5x."), _dossier())
    assert report.checked_count == 2
    assert report.supported_count == 2
    assert "2 of 2" in report.notes()[0]


# --- topic coherence -------------------------------------------------------


def test_topic_terms_drop_function_words():
    terms = topic_terms("The Rise of the Machines")
    assert "the" not in terms
    assert "machines" in terms


def test_topic_drift_is_flagged_when_research_is_about_something_else():
    # The investigation's original bug: a dairy-pricing brief returning
    # agent-swarm findings, with every statistic faithfully copied so the
    # grounding check passes cleanly and hides the mismatch.
    note = topic_coherence_note("Regional Dairy Pricing Volatility in Q3", _dossier())
    assert note is not None
    assert "Topic drift" in note


def test_no_topic_drift_when_research_matches_the_brief():
    assert topic_coherence_note("Enterprise AI adoption", _dossier()) is None


def test_topic_drift_ignores_the_dossier_echo_of_the_brief_topic():
    # ResearchDossier.topic is copied from the brief, so comparing against it
    # would make every dossier look relevant to every brief.
    dossier = _dossier()
    dossier.topic = "Regional Dairy Pricing Volatility"
    assert topic_coherence_note("Regional Dairy Pricing Volatility", dossier) is not None
