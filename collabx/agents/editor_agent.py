from collabx.core.editorial_graph import EditorialGraph
from collabx.core.ids import stable_suffix
from collabx.core.models import (
    ArticleDraft,
    EditorialBrief,
    PublishedNewsletter,
    ResearchDossier,
)

# Average adult reading speed, used to estimate read time.
WORDS_PER_MINUTE = 200


class EditorAgent:
    """
    EditorAgent: Performs fact-checking, readability scoring, tone audits, and publication formatting.
    """

    def __init__(self):
        self.name = "EditorAgent"
        self.version = "2.0.0"

    def review_and_publish(
        self,
        brief: EditorialBrief,
        draft: ArticleDraft,
        dossier: ResearchDossier,
        revision_rounds: int = 0,
    ) -> PublishedNewsletter:
        """Score the draft against the dossier and publish it with its verdict.

        Publication is unconditional. A draft that failed its gates is still
        returned, carrying `revision_required=True` and a critique naming each
        failure, so the endpoint stays total and the caller decides.
        """
        feedback = EditorialGraph.evaluate_draft(draft, brief, dossier)
        html_body = EditorialGraph.compile_html(draft.raw_markdown)
        read_time = max(1, round(draft.word_count / WORDS_PER_MINUTE))

        # Record how much revision the edition took. Without this the loop is
        # invisible to a caller: a first-pass draft and a twice-revised one
        # would be indistinguishable in the response.
        if revision_rounds:
            plural = "round" if revision_rounds == 1 else "rounds"
            outcome = (
                "gates still failing" if feedback.revision_required else "all gates passing"
            )
            feedback.critique_notes.append(
                f"Editorial loop: {revision_rounds} revision {plural} applied, "
                f"{outcome} at publication."
            )
        elif feedback.revision_required:
            # Do not say "no revision needed" here. Revision *was* needed; the
            # round budget was spent or set to zero, which is a different fact.
            feedback.critique_notes.append(
                "Editorial loop: no revision rounds were available, so the draft "
                "was published as first written despite failing its gates."
            )
        else:
            feedback.critique_notes.append(
                "Editorial loop: published on the first draft, no revision needed."
            )

        return PublishedNewsletter(
            edition_id=f"ED-{stable_suffix(brief.topic, 100000)}",
            title=draft.headline,
            subtitle=draft.subheadline,
            final_markdown=draft.raw_markdown,
            html_body=html_body,
            read_time_minutes=read_time,
            feedback=feedback,
            research_dossier=dossier,
        )
