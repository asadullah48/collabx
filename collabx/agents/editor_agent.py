from collabx.core.models import EditorialBrief, ArticleDraft, EditorFeedback, PublishedNewsletter, ResearchDossier
from collabx.core.editorial_graph import EditorialGraph

class EditorAgent:
    """
    EditorAgent: Performs fact-checking, readability scoring, tone audits, and publication formatting.
    """
    def __init__(self):
        self.name = "EditorAgent"
        self.version = "1.0.0"

    def review_and_publish(
        self, brief: EditorialBrief, draft: ArticleDraft, dossier: ResearchDossier
    ) -> PublishedNewsletter:
        feedback = EditorialGraph.evaluate_draft(draft, brief)
        html_body = EditorialGraph.compile_html(draft.raw_markdown)
        read_time = max(1, round(draft.word_count / 200))

        return PublishedNewsletter(
            edition_id=f"ED-{abs(hash(brief.topic)) % 100000}",
            title=draft.headline,
            subtitle=draft.subheadline,
            final_markdown=draft.raw_markdown,
            html_body=html_body,
            read_time_minutes=read_time,
            feedback=feedback,
            research_dossier=dossier
        )
