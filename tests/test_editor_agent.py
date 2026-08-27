import pytest
from collabx.agents.researcher_agent import ResearcherAgent
from collabx.agents.writer_agent import WriterAgent
from collabx.agents.editor_agent import EditorAgent
from collabx.core.models import EditorialBrief

def test_editor_agent_publication():
    researcher = ResearcherAgent()
    writer = WriterAgent()
    editor = EditorAgent()
    brief = EditorialBrief(topic="Autonomous Swarms in 2026")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)
    pub = editor.review_and_publish(brief, draft, dossier)
    
    assert pub.read_time_minutes >= 1
    assert pub.feedback.fact_check_passed is True
    assert "<h1>" in pub.html_body
