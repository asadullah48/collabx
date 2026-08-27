"""
CollabX: Orchestrated Multi-Agent Newsletter & Report Team Framework
"""

__version__ = "1.0.0"

from collabx.agents.researcher_agent import ResearcherAgent
from collabx.agents.writer_agent import WriterAgent
from collabx.agents.editor_agent import EditorAgent
from collabx.orchestration.collabx_engine import CollabXEngine

__all__ = [
    "ResearcherAgent",
    "WriterAgent",
    "EditorAgent",
    "CollabXEngine"
]
