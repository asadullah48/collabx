"""The Researcher supplies the dossier every later stage is checked against.

Three modes, in priority order:

1. **Caller-supplied** -- real research arrives with the request. This is the
   only mode where the Editor's fact-check means anything about the world.
2. **Model-generated** -- a language model drafts findings when a provider is
   configured. Clearly labelled `MODEL_GENERATED`, and **source URLs are never
   invented**: a fabricated citation that looks real is worse than no citation,
   because it survives a glance and fails an audit.
3. **Fixture** -- built-in sample findings, the zero-config default, so the
   project runs on a fresh clone with nothing installed.

A model cannot browse the web. That is the honest constraint this design is
built around, rather than papered over.
"""
from __future__ import annotations

import json
from typing import List, Optional

from collabx.core.ids import stable_suffix
from collabx.core.models import (
    DossierProvenance,
    EditorialBrief,
    ResearchDossier,
    ResearchFinding,
)
from collabx.providers import resolve_provider
from collabx.providers.base import ProviderUnavailable
from collabx.providers.deterministic import is_model_backed

# Marker used in place of a URL for model-drafted findings. Never a plausible
# domain: the point is that it cannot be mistaken for a real citation.
UNVERIFIED_SOURCE = "unverified://model-generated"

RESEARCH_PROMPT = """You are a research assistant preparing a briefing file.

Topic: {topic}
Audience: {audience}

Return exactly {count} findings as a JSON array. Each object must have:
  "headline"  - a short factual claim, under 10 words
  "statistic" - one sentence containing a specific figure, written as a percentage or a multiplier
  "quote"     - one sentence a practitioner might say about this

Rules:
- Output ONLY the JSON array. No prose, no markdown fences.
- Do NOT invent URLs, publication names, or attributions to real organisations.
- Keep every sentence under 20 words.

JSON array:"""


class ResearcherAgent:
    """
    ResearcherAgent: Gathers industry signals, statistics, verified quotes, and emerging themes.
    """

    def __init__(self, provider=None):
        self.name = "ResearcherAgent"
        self.version = "2.0.0"
        self.provider = provider if provider is not None else resolve_provider()

    def conduct_research(
        self,
        brief: EditorialBrief,
        supplied: Optional[ResearchDossier] = None,
    ) -> ResearchDossier:
        if supplied is not None:
            return self._adopt(supplied, brief)

        if is_model_backed(self.provider):
            generated = self._generate(brief)
            if generated is not None:
                return generated

        return self._fixture(brief)

    # -- mode 1: caller-supplied ------------------------------------------

    @staticmethod
    def _adopt(supplied: ResearchDossier, brief: EditorialBrief) -> ResearchDossier:
        """Take the caller's research, stamping provenance so it cannot be faked.

        Provenance is set here rather than trusted from the request body. A
        caller could otherwise post model slop labelled CALLER_SUPPLIED and the
        response would vouch for it.
        """
        return supplied.model_copy(
            update={
                "provenance": DossierProvenance.CALLER_SUPPLIED,
                "topic": supplied.topic or brief.topic,
            }
        )

    # -- mode 2: model-generated ------------------------------------------

    def _generate(self, brief: EditorialBrief) -> Optional[ResearchDossier]:
        """Draft findings with the configured model, or return None to fall back."""
        prompt = RESEARCH_PROMPT.format(
            topic=brief.topic, audience=brief.target_audience, count=3
        )
        try:
            raw = self.provider.complete(prompt, max_tokens=900, temperature=0.4)
        except ProviderUnavailable:
            return None

        findings = self._parse_findings(raw)
        if not findings:
            return None

        return ResearchDossier(
            dossier_id=f"DOS-{stable_suffix(brief.topic, 10000)}",
            topic=brief.topic,
            findings=findings,
            core_themes=[f.headline for f in findings[:3]],
            provenance=DossierProvenance.MODEL_GENERATED,
        )

    @staticmethod
    def _parse_findings(raw: str) -> List[ResearchFinding]:
        """Parse the model's JSON array, tolerating the usual wrapper noise."""
        text = raw.strip()
        if text.startswith("```"):
            # Strip a fenced block, with or without a language tag.
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return []

        try:
            items = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
        if not isinstance(items, list):
            return []

        findings: List[ResearchFinding] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            headline = str(item.get("headline", "")).strip()
            statistic = str(item.get("statistic", "")).strip()
            quote = str(item.get("quote", "")).strip()
            if not (headline and statistic):
                continue
            findings.append(
                ResearchFinding(
                    headline=headline,
                    statistic=statistic,
                    # Never a plausible-looking domain, even if the model
                    # offered one. An invented citation is the worst output
                    # this system could produce.
                    source_url=UNVERIFIED_SOURCE,
                    verified_quote=quote or statistic,
                )
            )
        return findings

    # -- mode 3: fixture ---------------------------------------------------

    @staticmethod
    def _fixture(brief: EditorialBrief) -> ResearchDossier:
        findings = [
            ResearchFinding(
                headline="Enterprise Multi-Agent Orchestration Adoption Accelerates",
                statistic="78% of Fortune 500 engineering teams deploy autonomous agent loops in 2026.",
                source_url="https://gartner.com/research/agent-orchestration-2026",
                verified_quote="Autonomous agents are shifting enterprise productivity from assist to execute.",
            ),
            ResearchFinding(
                headline="Deterministic Workflows Surpass Unstructured Prompting",
                statistic="3.4x reduction in workflow execution errors with state-machine orchestration.",
                source_url="https://bloomberg.com/tech/ai-agent-reliability-index",
                verified_quote="Orchestrated agent teams eliminate hallucinations through peer verification.",
            ),
        ]

        return ResearchDossier(
            dossier_id=f"DOS-{stable_suffix(brief.topic, 10000)}",
            topic=brief.topic,
            findings=findings,
            core_themes=[
                "Autonomous Workflows",
                "State Machine Reliability",
                "Human-in-the-Loop Governance",
            ],
            provenance=DossierProvenance.FIXTURE,
        )
