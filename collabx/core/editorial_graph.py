"""Editorial evaluation and publication formatting.

`evaluate_draft` used to return three constants. It now runs three real gates
and reports the margin on each:

    readability   Flesch Reading Ease against the tone's floor (tone.py)
    grounding     statistics and quotations traced to the dossier (grounding.py)
    tone          sentence length and long-word density against the tone profile

Word count is reported but is **not** a gate. The Writer composes from the
dossier and cannot honestly pad to an arbitrary target, so a shortfall is an
editorial signal about the brief or the research, not a defect in the draft.

When the loop exhausts its budget with gates still failing, the edition is
published anyway with `revision_required=True` and a critique naming each
failure. The endpoint stays total; the verdict carries the bad news.
"""
from dataclasses import dataclass
from html import escape
from typing import List

from collabx.core.grounding import check_grounding, topic_coherence_note
from collabx.core.models import (
    ArticleDraft,
    EditorFeedback,
    EditorialBrief,
    ResearchDossier,
)
from collabx.core.readability import flesch_reading_ease
from collabx.core.tone import profile_for, tone_alignment, tone_diagnostics


@dataclass(frozen=True)
class QualityGate:
    """One pass/fail check, with the margin that decided it."""

    name: str
    passed: bool
    detail: str


class EditorialGraph:
    """
    EditorialGraph: Manages collaborative state transitions between Researcher, Writer, and Editor agents,
    supporting automated revision loops if readability falls below threshold.
    """

    # Minimum acceptable tone alignment. Both proxies (sentence length, long-word
    # density) score 1.0 inside the tone's envelope, so 0.75 tolerates one proxy
    # overshooting its target by half before the gate trips.
    TONE_ALIGNMENT_FLOOR = 0.75

    @staticmethod
    def gates_for(
        draft: ArticleDraft, brief: EditorialBrief, dossier: ResearchDossier
    ) -> List[QualityGate]:
        """Run every quality gate against `draft`, returning each with its margin."""
        profile = profile_for(brief.tone)
        markdown = draft.raw_markdown

        readability = flesch_reading_ease(markdown)
        readability_ok = readability >= profile.readability_floor
        readability_detail = (
            f"Readability (Flesch Reading Ease) is {readability:.1f} against a "
            f"{profile.readability_floor:.0f} floor for '{profile.label}'."
        )
        if not readability_ok:
            readability_detail += (
                f" Short by {profile.readability_floor - readability:.1f} points."
            )

        grounding = check_grounding(draft, dossier)

        alignment = tone_alignment(markdown, brief.tone)
        alignment_ok = alignment >= EditorialGraph.TONE_ALIGNMENT_FLOOR
        alignment_detail = (
            f"Tone alignment with '{profile.label}' is {alignment:.2f} against a "
            f"{EditorialGraph.TONE_ALIGNMENT_FLOOR:.2f} floor."
        )

        return [
            QualityGate("readability", readability_ok, readability_detail),
            QualityGate("grounding", grounding.passed, " ".join(grounding.notes())),
            QualityGate("tone_alignment", alignment_ok, alignment_detail),
        ]

    @staticmethod
    def evaluate_draft(
        draft: ArticleDraft, brief: EditorialBrief, dossier: ResearchDossier
    ) -> EditorFeedback:
        """Score `draft` and decide whether it needs another revision round."""
        markdown = draft.raw_markdown

        readability = flesch_reading_ease(markdown)
        alignment = tone_alignment(markdown, brief.tone)
        grounding = check_grounding(draft, dossier)
        gates = EditorialGraph.gates_for(draft, brief, dossier)

        notes: List[str] = [gate.detail for gate in gates]
        notes.extend(tone_diagnostics(markdown, brief.tone))
        notes.append(EditorialGraph._length_note(markdown, brief))

        drift = topic_coherence_note(brief.topic, dossier)
        if drift:
            notes.append(drift)

        failed = [gate.name for gate in gates if not gate.passed]
        if failed:
            notes.append(f"Revision required. Failing gates: {', '.join(failed)}.")

        return EditorFeedback(
            readability_score=readability,
            fact_check_passed=grounding.passed,
            tone_alignment_score=alignment,
            critique_notes=notes,
            revision_required=bool(failed),
        )

    @staticmethod
    def _length_note(markdown: str, brief: EditorialBrief) -> str:
        """Report length against the brief target. Reported, never gated."""
        word_count = len(markdown.split())
        target = brief.target_word_count
        if word_count >= target:
            return f"Word count ({word_count} words) meets the {target}-word brief target."
        return (
            f"Word count ({word_count} words) is {target - word_count} short of the "
            f"{target}-word brief target. The draft is composed from the research "
            f"dossier, so a shortfall usually means the research is thinner than "
            f"the brief assumes."
        )

    @staticmethod
    def compile_html(markdown_text: str) -> str:
        # Lightweight markdown to HTML formatter.
        # Every slice is escaped before interpolation: the brief topic is
        # user-controlled and flows through the headline into this output, and
        # html_body is documented as an email-broadcast payload. quote=False is
        # deliberate -- these are text nodes, not attributes, so escaping the
        # article's own apostrophes would corrupt the prose for no security gain.
        def text(raw: str) -> str:
            return escape(raw, quote=False)

        lines = markdown_text.split('\n')
        html_lines = []
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f"<h1>{text(line[2:])}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{text(line[3:])}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{text(line[4:])}</h3>")
            elif line.startswith('> '):
                html_lines.append(f"<blockquote>{text(line[2:])}</blockquote>")
            elif line.strip():
                html_lines.append(f"<p>{text(line)}</p>")
        return "\n".join(html_lines)
