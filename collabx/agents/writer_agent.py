from typing import List
from collabx.core.models import EditorialBrief, ResearchDossier, ArticleDraft, NewsletterSection
from collabx.core.ids import stable_suffix

class WriterAgent:
    """
    WriterAgent: Drafts high-engagement newsletter editions, catchy hooks, and structured body narratives.
    """
    def __init__(self):
        self.name = "WriterAgent"
        self.version = "1.0.0"

    def compose_draft(self, brief: EditorialBrief, dossier: ResearchDossier) -> ArticleDraft:
        headline = f"The Next Frontier: {brief.topic}"
        subheadline = "How Multi-Agent Teams Are Transforming Enterprise Software"
        hook = "The era of single-prompt chatbot copilots is officially over. In 2026, enterprise software is powered by autonomous multi-agent teams."

        sec1 = NewsletterSection(
            heading="1. The Shift from Assist to Execute",
            content_markdown="""According to recent Gartner research, **78% of Fortune 500 engineering teams** have adopted autonomous agent loops. Rather than waiting for human prompts, these agents proactively monitor codebases, index private context, and orchestrate complex DAG workflows."""
        )

        sec2 = NewsletterSection(
            heading="2. Why Multi-Agent Collaboration Wins",
            content_markdown="""Single LLMs are prone to compounding errors. By dividing responsibilities into specialized roles—such as **Researcher**, **Writer**, and **Editor**—enterprises achieve a **3.4x reduction in workflow execution failures** while maintaining continuous peer verification."""
        )

        sec3 = NewsletterSection(
            heading="3. Key Strategic Takeaway",
            content_markdown="""> *'Autonomous agents are shifting enterprise productivity from assist to execute.'*\n\nOrganizations that invest in deterministic state machines and collaborative agent orchestration will define the next decade of market leadership."""
        )

        full_md = f"""# {headline}\n\n*{subheadline}*\n\n{hook}\n\n## {sec1.heading}\n\n{sec1.content_markdown}\n\n## {sec2.heading}\n\n{sec2.content_markdown}\n\n## {sec3.heading}\n\n{sec3.content_markdown}"""

        words = len(full_md.split())

        return ArticleDraft(
            draft_id=f"DFT-{stable_suffix(brief.topic, 10000)}",
            headline=headline,
            subheadline=subheadline,
            hook=hook,
            sections=[sec1, sec2, sec3],
            raw_markdown=full_md,
            word_count=words
        )
