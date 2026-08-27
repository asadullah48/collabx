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

class ResearchDossier(BaseModel):
    dossier_id: str
    topic: str
    findings: List[ResearchFinding]
    core_themes: List[str]
    compiled_at: float = Field(default_factory=time.time)

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
