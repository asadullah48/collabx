import pytest
from collabx.agents.researcher_agent import ResearcherAgent
from collabx.agents.writer_agent import WriterAgent
from collabx.core.models import EditorialBrief

def test_writer_agent_composition():
    researcher = ResearcherAgent()
    writer = WriterAgent()
    brief = EditorialBrief(topic="Multi-Agent Systems")
    dossier = researcher.conduct_research(brief)
    draft = writer.compose_draft(brief, dossier)
    
    assert len(draft.sections) == 3
    assert draft.word_count > 50
    assert draft.headline.startswith("The Next Frontier:")
