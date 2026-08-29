import pytest

from collabx.core.editorial_graph import EditorialGraph
from collabx.core.models import (
    ArticleDraft,
    EditorialBrief,
    NewsletterSection,
    ResearchDossier,
    ResearchFinding,
    ToneStyle,
)
from collabx.core.tone import profile_for


def _dossier(**overrides) -> ResearchDossier:
    finding = ResearchFinding(
        headline="Enterprise AI adoption climbs",
        statistic="61% of teams shipped an agent feature this year.",
        source_url="https://example.com/research/enterprise-ai",
        verified_quote="Adoption moved from pilots to production.",
    )
    defaults = dict(
        dossier_id="DOS-1",
        topic="Enterprise AI",
        findings=[finding],
        core_themes=["Enterprise AI adoption"],
    )
    defaults.update(overrides)
    return ResearchDossier(**defaults)


def _draft(markdown: str, word_count: int = 50) -> ArticleDraft:
    return ArticleDraft(
        draft_id="D1",
        headline="Enterprise AI Rising",
        subheadline="The multi-agent transition",
        hook="Intro hook",
        sections=[NewsletterSection(heading="Sec1", content_markdown="Content")],
        raw_markdown=markdown,
        word_count=word_count,
    )


def _plain_draft() -> ArticleDraft:
    # Short plain sentences that clear the readability floor for every tone.
    return _draft(
        "The team shipped it. 61% of teams shipped an agent feature this year. "
        "The work was slow. Then it was fast. Most teams saw the same shift."
    )


def test_evaluate_draft_scores_real_readability_not_a_constant():
    brief = EditorialBrief(topic="Enterprise AI")
    easy = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    hard = EditorialGraph.evaluate_draft(
        _draft(
            "Heterogeneous orchestration methodologies substantially facilitate "
            "the compounding operationalization of autonomous organizational "
            "capabilities across multinational enterprise infrastructures."
        ),
        brief,
        _dossier(),
    )
    # The whole point of removing the placeholder: the score has to move.
    assert easy.readability_score > hard.readability_score
    assert 0.0 <= hard.readability_score <= 100.0


def test_readability_gate_uses_the_tone_floor_not_a_global_threshold():
    # The same draft is acceptable for a dense analyst voice and not for a
    # storyteller voice, because the floors differ.
    # Scores ~41.5: above the analyst floor of 30, below the storyteller's 55.
    # A single global threshold could not produce different verdicts here.
    markdown = (
        "The teams that adopted agents reported fewer errors in production, and "
        "their architects say the systems are now easier to reason about than before."
    )
    analyst = EditorialGraph.evaluate_draft(
        _draft(markdown), EditorialBrief(tone=ToneStyle.DEEP_DIVE_ANALYST), _dossier()
    )
    storyteller = EditorialGraph.evaluate_draft(
        _draft(markdown), EditorialBrief(tone=ToneStyle.ENGAGING_STORYTELLER), _dossier()
    )
    assert analyst.readability_score == storyteller.readability_score
    assert (
        profile_for(ToneStyle.DEEP_DIVE_ANALYST).readability_floor
        < profile_for(ToneStyle.ENGAGING_STORYTELLER).readability_floor
    )
    assert storyteller.revision_required
    assert not any("Short by" in note for note in analyst.critique_notes)


SPRAWLING = (
    "Heterogeneous orchestration methodologies substantially facilitate the "
    "compounding operationalization of autonomous organizational capabilities "
    "across multinational enterprise infrastructure modernization programmes, "
    "and numerous organizations demonstrate significantly improved delivery "
    "characteristics throughout their transformation portfolios."
)


def test_tone_alignment_score_in_feedback_reflects_the_draft():
    # The reported score must be derived from the text, not attached to it.
    # A constant would make these two identical.
    brief = EditorialBrief(topic="Enterprise AI")
    plain = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    sprawling = EditorialGraph.evaluate_draft(_draft(SPRAWLING), brief, _dossier())
    assert plain.tone_alignment_score > sprawling.tone_alignment_score


def test_tone_alignment_gate_can_actually_fail():
    # A gate that no input can trip is not a gate.
    brief = EditorialBrief(topic="Enterprise AI")
    feedback = EditorialGraph.evaluate_draft(_draft(SPRAWLING), brief, _dossier())
    assert feedback.tone_alignment_score < EditorialGraph.TONE_ALIGNMENT_FLOOR
    assert "tone_alignment" in next(
        n for n in feedback.critique_notes if "Failing gates" in n
    )


def test_fact_check_fails_on_a_statistic_absent_from_the_dossier():
    brief = EditorialBrief(topic="Enterprise AI")
    feedback = EditorialGraph.evaluate_draft(
        _draft("The team shipped it. A remarkable 94% of teams agreed. It was fast."),
        brief,
        _dossier(),
    )
    assert feedback.fact_check_passed is False
    assert any("94%" in note for note in feedback.critique_notes)


def test_fact_check_passes_when_every_statistic_traces_to_the_dossier():
    brief = EditorialBrief(topic="Enterprise AI")
    feedback = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    assert feedback.fact_check_passed is True


def test_topic_drift_is_reported_when_research_does_not_match_the_brief():
    brief = EditorialBrief(topic="Regional Dairy Pricing Volatility")
    feedback = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    assert any("Topic drift" in note for note in feedback.critique_notes)


def test_no_topic_drift_reported_when_research_matches_the_brief():
    brief = EditorialBrief(topic="Enterprise AI adoption")
    feedback = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    assert not any("Topic drift" in note for note in feedback.critique_notes)


def test_editorial_graph_html_compilation():
    md = "# Main Title\n## Section Heading\n> Featured quote\nParagraph body text."
    html = EditorialGraph.compile_html(md)
    assert "<h1>Main Title</h1>" in html
    assert "<h2>Section Heading</h2>" in html
    assert "<blockquote>Featured quote</blockquote>" in html
    assert "<p>Paragraph body text.</p>" in html


def _draft_with_word_count(n: int) -> ArticleDraft:
    body = " ".join(["word"] * n)
    return _draft(body, word_count=n)


def test_critique_reports_shortfall_when_draft_is_under_target():
    brief = EditorialBrief(topic="Enterprise AI", target_word_count=200)
    feedback = EditorialGraph.evaluate_draft(
        _draft_with_word_count(150), brief, _dossier()
    )
    note = next(n for n in feedback.critique_notes if "Word count" in n)
    assert "50 short" in note
    assert "meets" not in note


def test_critique_reports_target_met_when_draft_is_long_enough():
    brief = EditorialBrief(topic="Enterprise AI", target_word_count=100)
    feedback = EditorialGraph.evaluate_draft(
        _draft_with_word_count(150), brief, _dossier()
    )
    note = next(n for n in feedback.critique_notes if "Word count" in n)
    assert "meets" in note
    assert "short of" not in note


def test_word_count_shortfall_alone_does_not_force_a_revision():
    # Length is reported, never gated: the Writer composes from the dossier and
    # cannot honestly pad to an arbitrary target.
    brief = EditorialBrief(topic="Enterprise AI", target_word_count=5000)
    feedback = EditorialGraph.evaluate_draft(_plain_draft(), brief, _dossier())
    assert any("short of" in note for note in feedback.critique_notes)
    assert feedback.revision_required is False


def test_revision_required_is_true_exactly_when_a_gate_fails():
    brief = EditorialBrief(topic="Enterprise AI")
    draft = _draft("The team shipped it. A remarkable 94% of teams agreed. It was fast.")
    gates = EditorialGraph.gates_for(draft, brief, _dossier())
    feedback = EditorialGraph.evaluate_draft(draft, brief, _dossier())
    assert feedback.revision_required == any(not gate.passed for gate in gates)
    assert feedback.revision_required is True


def test_failing_gates_are_named_in_the_critique():
    brief = EditorialBrief(topic="Enterprise AI")
    feedback = EditorialGraph.evaluate_draft(
        _draft("The team shipped it. A remarkable 94% of teams agreed. It was fast."),
        brief,
        _dossier(),
    )
    note = next(n for n in feedback.critique_notes if "Failing gates" in n)
    assert "grounding" in note


def test_compile_html_escapes_markup_in_headings():
    # The brief topic is user-controlled and reaches compile_html via the
    # headline, so a topic carrying markup must not become live HTML.
    html = EditorialGraph.compile_html("# The Next Frontier: <img src=x onerror=alert(1)>")
    assert "<img" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_compile_html_escapes_markup_in_body_and_quotes():
    md = "> <script>steal()</script>\nBody with <b>tags</b> & an ampersand."
    html = EditorialGraph.compile_html(md)
    assert "<script>" not in html
    assert "<b>" not in html
    assert "&lt;script&gt;steal()&lt;/script&gt;" in html
    assert "&amp; an ampersand" in html


def test_compile_html_leaves_prose_punctuation_readable():
    # quote=False: apostrophes and quotation marks stay literal so the email
    # body reads as prose rather than entity soup.
    html = EditorialGraph.compile_html("> *'Agents shift productivity from assist to execute.'*")
    assert "&#x27;" not in html
    assert "'Agents shift productivity" in html
