import pytest
from collabx.core.editorial_graph import EditorialGraph
from collabx.core.models import ArticleDraft, EditorialBrief, NewsletterSection

def test_editorial_graph_evaluation():
    brief = EditorialBrief(topic="Enterprise AI")
    draft = ArticleDraft(
        draft_id="D1",
        headline="Enterprise AI Rising",
        subheadline="The multi-agent transition",
        hook="Intro hook",
        sections=[NewsletterSection(heading="Sec1", content_markdown="Content")],
        raw_markdown="# Enterprise AI Rising\n\nIntro content body paragraph.",
        word_count=50
    )
    feedback = EditorialGraph.evaluate_draft(draft, brief)
    assert feedback.fact_check_passed is True
    assert feedback.readability_score >= 80.0
    assert feedback.revision_required is False

def test_editorial_graph_html_compilation():
    md = "# Main Title\n## Section Heading\n> Featured quote\nParagraph body text."
    html = EditorialGraph.compile_html(md)
    assert "<h1>Main Title</h1>" in html
    assert "<h2>Section Heading</h2>" in html
    assert "<blockquote>Featured quote</blockquote>" in html
    assert "<p>Paragraph body text.</p>" in html
