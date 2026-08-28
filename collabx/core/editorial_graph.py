from typing import Dict, Any, Tuple
from collabx.core.models import (
    EditorialBrief, ResearchDossier, ArticleDraft, EditorFeedback, PublishedNewsletter
)

class EditorialGraph:
    """
    EditorialGraph: Manages collaborative state transitions between Researcher, Writer, and Editor agents,
    supporting automated revision loops if readability falls below threshold.
    """
    # Readability gate from SPEC.md section 3.
    READABILITY_THRESHOLD = 80.0

    # NOTE: `readability_score`, `fact_check_passed`, and `tone_alignment_score` are
    # fixed placeholder values. No Flesch-Kincaid calculation and no dossier grounding
    # check are implemented yet, so these numbers describe nothing about the draft.
    # Only the word-count note below is derived from the actual draft.
    PLACEHOLDER_READABILITY = 88.5
    PLACEHOLDER_TONE_ALIGNMENT = 0.94

    @staticmethod
    def evaluate_draft(draft: ArticleDraft, brief: EditorialBrief) -> EditorFeedback:
        word_count = len(draft.raw_markdown.split())
        readability = EditorialGraph.PLACEHOLDER_READABILITY
        tone_score = EditorialGraph.PLACEHOLDER_TONE_ALIGNMENT
        fact_check = True

        # Report what the word count actually is relative to the brief, rather than
        # asserting it satisfies the target unconditionally.
        target = brief.target_word_count
        if word_count >= target:
            length_note = f"Word count ({word_count} words) meets the {target}-word brief target."
        else:
            shortfall = target - word_count
            length_note = (
                f"Word count ({word_count} words) is {shortfall} short of the "
                f"{target}-word brief target."
            )

        notes = [
            f"Hook and narrative structure reviewed against tone '{brief.tone.value}'.",
            length_note,
            "Readability, tone, and fact-check scores are placeholders; "
            "no automated verification is implemented yet."
        ]

        return EditorFeedback(
            readability_score=readability,
            fact_check_passed=fact_check,
            tone_alignment_score=tone_score,
            critique_notes=notes,
            revision_required=readability < EditorialGraph.READABILITY_THRESHOLD
        )

    @staticmethod
    def compile_html(markdown_text: str) -> str:
        # Lightweight markdown to HTML formatter
        lines = markdown_text.split('\n')
        html_lines = []
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith('> '):
                html_lines.append(f"<blockquote>{line[2:]}</blockquote>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")
        return "\n".join(html_lines)
