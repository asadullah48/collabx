import pytest
from collabx.agents.researcher_agent import ResearcherAgent
from collabx.core.models import EditorialBrief

def test_researcher_agent_findings():
    agent = ResearcherAgent()
    brief = EditorialBrief(topic="Autonomous Agent Swarms")
    dossier = agent.conduct_research(brief)
    assert len(dossier.findings) >= 2
    assert len(dossier.core_themes) >= 2
    assert "Gartner" in dossier.findings[0].headline or "Adoption" in dossier.findings[0].headline
