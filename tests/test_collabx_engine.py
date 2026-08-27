import pytest
from collabx.orchestration.collabx_engine import CollabXEngine
from collabx.core.models import EditorialBrief

def test_collabx_engine_end_to_end():
    engine = CollabXEngine()
    brief = EditorialBrief(topic="Enterprise Agent Workforces")
    pub = engine.produce_edition(brief)
    
    assert len(pub.research_dossier.findings) >= 2
    assert pub.feedback.readability_score >= 80.0
    assert pub.title.startswith("The Next Frontier:")
