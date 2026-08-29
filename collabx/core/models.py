from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time

class ToneStyle(str, Enum):
    TECH_PIONEER = "TECH_PIONEER"
    EXECUTIVE_BRIEF = "EXECUTIVE_BRIEF"
    DEEP_DIVE_ANALYST = "DEEP_DIVE_ANALYST"
    ENGAGING_STORYTELLER = "ENGAGING_STORYTELLER"

class EditorialBrief(BaseModel):
    brief_id: str = "BRIEF-101"
    topic: str = "The Rise of Autonomous Agent Swarms in Enterprise Automation"
    target_audience: str = "CTOs, Founders & Enterprise Architects"
    tone: ToneStyle = ToneStyle.TECH_PIONEER
    target_word_count: int = 650

class ResearchFinding(BaseModel):
    headline: str
    statistic: str
    source_url: str
    verified_quote: str

class DossierProvenance(str, Enum):
    """Where a dossier's findings came from.

    This is the most important field in the response. The Editor verifies the
    Writer's statistics against the dossier, so the whole fact-check is only as
    trustworthy as the research behind it. A model-generated dossier means the
    check compares one generated text against another and proves nothing about
    the world -- so it is labelled, never silently presented as verification.
    """

    FIXTURE = "FIXTURE"                    # built-in sample data, same for every topic
    CALLER_SUPPLIED = "CALLER_SUPPLIED"    # real research provided with the request
    MODEL_GENERATED = "MODEL_GENERATED"    # written by a language model, unverified


class ResearchDossier(BaseModel):
    dossier_id: str
    topic: str
    findings: List[ResearchFinding]
    core_themes: List[str]
    provenance: DossierProvenance = DossierProvenance.FIXTURE
    compiled_at: float = Field(default_factory=time.time)

    @property
    def is_verifiable(self) -> bool:
        """True only when the findings came from outside this process."""
        return self.provenance is DossierProvenance.CALLER_SUPPLIED

class NewsletterSection(BaseModel):
    heading: str
    content_markdown: str

class ArticleDraft(BaseModel):
    draft_id: str
    headline: str
    subheadline: str
    hook: str
    sections: List[NewsletterSection]
    raw_markdown: str
    word_count: int

class EditorFeedback(BaseModel):
    readability_score: float # 0 - 100 (Flesch-Kincaid)
    fact_check_passed: bool
    tone_alignment_score: float # 0.0 - 1.0
    critique_notes: List[str]
    revision_required: bool

class EditorialRequest(EditorialBrief):
    """A brief, optionally carrying research the caller already gathered.

    Inherits from `EditorialBrief` so the request body stays flat and every
    existing client keeps working: `{"topic": "..."}` is still valid. Adding
    `dossier` opts into the mode that makes the fact-check meaningful --
    real sources in, verified newsletter out.
    """

    dossier: Optional[ResearchDossier] = Field(
        default=None,
        description=(
            "Research to write from. When supplied, the Researcher is skipped "
            "and the Editor verifies every statistic and quotation against "
            "these findings."
        ),
    )


class PublishedNewsletter(BaseModel):
    edition_id: str
    title: str
    subtitle: str
    final_markdown: str
    html_body: str
    read_time_minutes: int
    feedback: EditorFeedback
    research_dossier: ResearchDossier
    published_at: float = Field(default_factory=time.time)
