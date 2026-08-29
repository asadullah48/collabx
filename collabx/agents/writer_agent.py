"""The Writer composes a draft from the brief and the dossier.

This is a **template-based deterministic writer, not a language model.** It
assembles prose from the Researcher's findings using per-tone sentence
patterns. Same brief plus same dossier always yields the same draft.

What changed from the original: the draft is now derived from its inputs.
Every statistic and quotation is copied verbatim out of a `ResearchFinding`,
so the Editor's grounding check has something real to verify, and `brief.tone`
and `brief.target_word_count` drive register and length instead of being
ignored entirely.
"""
from typing import List, Optional
from urllib.parse import urlparse

from collabx.core.ids import stable_suffix
from collabx.core.models import (
    ArticleDraft,
    EditorialBrief,
    NewsletterSection,
    ResearchDossier,
    ResearchFinding,
    ToneStyle,
)
from collabx.core.revision import apply_revisions
from collabx.core.tone import profile_for
from collabx.providers import resolve_provider
from collabx.providers.base import ProviderUnavailable
from collabx.providers.deterministic import is_model_backed

# Headline register per tone. TECH_PIONEER keeps "The Next Frontier:" because
# that is the published headline convention for the default brief.
HEADLINE_PREFIX = {
    ToneStyle.TECH_PIONEER: "The Next Frontier:",
    ToneStyle.EXECUTIVE_BRIEF: "Briefing:",
    ToneStyle.DEEP_DIVE_ANALYST: "In Depth:",
    ToneStyle.ENGAGING_STORYTELLER: "The Story Behind",
}

SUBHEADLINE = {
    ToneStyle.TECH_PIONEER: "What the shift means for the teams building it",
    ToneStyle.EXECUTIVE_BRIEF: "What to know, and what to do about it",
    ToneStyle.DEEP_DIVE_ANALYST: "The evidence, and what it does not yet show",
    ToneStyle.ENGAGING_STORYTELLER: "How this began, and where it goes next",
}

# Openers are short and plain on purpose. The hook is the first thing scored
# and the first thing read, so density here costs twice.
HOOK = {
    ToneStyle.TECH_PIONEER: (
        "The tools changed faster than the teams using them. "
        "Here is what the data shows now."
    ),
    ToneStyle.EXECUTIVE_BRIEF: (
        "Here is the short version. The numbers below are the ones to act on."
    ),
    ToneStyle.DEEP_DIVE_ANALYST: (
        "The headline claims are easy to repeat and harder to check. "
        "This edition works through what the research supports."
    ),
    ToneStyle.ENGAGING_STORYTELLER: (
        "It started as a small change. Then it spread, and the way teams "
        "work was not the same."
    ),
}

CLOSING = {
    ToneStyle.TECH_PIONEER: "The teams who move first set the defaults everyone else gets.",
    ToneStyle.EXECUTIVE_BRIEF: "Decide where you stand before the next planning cycle.",
    ToneStyle.DEEP_DIVE_ANALYST: "The evidence points one way. The size of the effect is still open.",
    ToneStyle.ENGAGING_STORYTELLER: "The next part is being written by the teams reading this.",
}

# Plain connective sentences used to elaborate a finding. Each is generic
# because a template writer has no knowledge beyond the dossier -- it must not
# invent detail it cannot ground. Path 3 replaces these with model output.
ELABORATION = [
    "That number comes from the research file for this edition.",
    "It is a measured result, not a forecast.",
    "The effect shows up in teams of very different size.",
    "Check it against your own numbers before you act on it.",
    "The trend has held long enough to plan around.",
]

TAKEAWAY_HEADING = "What This Means"


class RevisionHint:
    """What the Editor asks the Writer to change on a revision round.

    Deliberately a plain object, not a pydantic model: it never crosses the API
    boundary. It is loop-internal instruction, not part of the response schema.

    `critique` carries the Editor's actual notes. On the template path they are
    unused -- a regex cannot act on prose -- but on the model path they are the
    whole point: the model is told which gate it failed and by how much, which
    turns the loop into a real critique-and-revise cycle rather than a retry.
    """

    def __init__(
        self,
        max_sentence_words: int,
        simplify_vocabulary: bool,
        critique: Optional[List[str]] = None,
    ):
        self.max_sentence_words = max_sentence_words
        self.simplify_vocabulary = simplify_vocabulary
        self.critique = critique or []

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"RevisionHint(max_sentence_words={self.max_sentence_words}, "
            f"simplify_vocabulary={self.simplify_vocabulary}, "
            f"critique={len(self.critique)} notes)"
        )


WRITER_PROMPT = """You are writing one section of a newsletter.

Topic: {topic}
Audience: {audience}
Voice: {tone_label} -- {guidance}

Use ONLY these research findings. Copy every figure EXACTLY as written:
{findings}

Write the newsletter body in markdown:
- Start with a one-line hook. No heading above it.
- Then one "## " section per finding, quoting that finding's figure verbatim.
- End with a "## What This Means" section.
- Average sentence length under {max_words} words.
- Do NOT invent any statistic, percentage, or quotation that is not listed above.
- Do NOT write a "# " title. Output markdown only, no commentary.
{critique_block}
Newsletter body:"""

CRITIQUE_HEADER = """
The previous draft was rejected by the editor. Fix these problems:
{notes}
"""


class WriterAgent:
    """
    WriterAgent: Drafts high-engagement newsletter editions, catchy hooks, and structured body narratives.
    """

    def __init__(self, provider=None):
        self.name = "WriterAgent"
        self.version = "3.0.0"
        self.provider = provider if provider is not None else resolve_provider()

    def compose_draft(
        self,
        brief: EditorialBrief,
        dossier: ResearchDossier,
        revision_hint: Optional[RevisionHint] = None,
    ) -> ArticleDraft:
        """Compose a draft. `revision_hint` re-runs composition under tighter limits.

        Tries the model first when one is configured, and falls back to the
        template on any failure. The fallback is silent by design: a draft
        produced without a model is a *worse* draft, not a failed request, and
        the Editor scores whichever one arrives by exactly the same rules.
        """
        if is_model_backed(self.provider):
            drafted = self._compose_with_model(brief, dossier, revision_hint)
            if drafted is not None:
                return drafted

        return self._compose_from_template(brief, dossier, revision_hint)

    def _compose_from_template(
        self,
        brief: EditorialBrief,
        dossier: ResearchDossier,
        revision_hint: Optional[RevisionHint] = None,
    ) -> ArticleDraft:
        headline = f"{HEADLINE_PREFIX[brief.tone]} {brief.topic}"
        subheadline = SUBHEADLINE[brief.tone]
        hook = HOOK[brief.tone]

        depth = self._elaboration_depth(brief.target_word_count, len(dossier.findings))
        sections = [
            self._section_for(finding, depth, index)
            for index, finding in enumerate(dossier.findings)
        ]
        sections.append(self._takeaway_section(dossier, brief))

        full_md = self._render(headline, subheadline, hook, sections)

        if revision_hint is not None:
            full_md = apply_revisions(
                full_md,
                max_sentence_words=revision_hint.max_sentence_words,
                simplify=revision_hint.simplify_vocabulary,
            )

        return ArticleDraft(
            draft_id=f"DFT-{stable_suffix(brief.topic, 10000)}",
            headline=headline,
            subheadline=subheadline,
            hook=hook,
            sections=sections,
            raw_markdown=full_md,
            word_count=len(full_md.split()),
        )

    # -- model path --------------------------------------------------------

    def _compose_with_model(
        self,
        brief: EditorialBrief,
        dossier: ResearchDossier,
        revision_hint: Optional[RevisionHint],
    ) -> Optional[ArticleDraft]:
        """Draft with the configured model, or return None to fall back."""
        profile = profile_for(brief.tone)

        findings = "\n".join(
            f'- {f.headline}: "{f.statistic}" (quotable: "{f.verified_quote}")'
            for f in dossier.findings
        )
        critique_block = ""
        if revision_hint is not None and revision_hint.critique:
            notes = "\n".join(f"- {n}" for n in revision_hint.critique)
            critique_block = CRITIQUE_HEADER.format(notes=notes)

        max_words = (
            revision_hint.max_sentence_words
            if revision_hint is not None
            else profile.target_sentence_words
        )

        prompt = WRITER_PROMPT.format(
            topic=brief.topic,
            audience=brief.target_audience,
            tone_label=profile.label,
            guidance=profile.guidance,
            findings=findings or "- (no findings supplied)",
            max_words=max_words,
            critique_block=critique_block,
        )

        try:
            body = self.provider.complete(prompt, max_tokens=1600, temperature=0.5)
        except ProviderUnavailable:
            return None

        body = self._strip_fences(body)
        sections = self._sections_from_markdown(body)
        if not sections:
            # A response with no headings is not a newsletter. Fall back rather
            # than publish a wall of text the Editor cannot section.
            return None

        headline = f"{HEADLINE_PREFIX[brief.tone]} {brief.topic}"
        subheadline = SUBHEADLINE[brief.tone]
        hook = body.split("\n", 1)[0].strip() or HOOK[brief.tone]

        full_md = f"# {headline}\n\n*{subheadline}*\n\n{body.strip()}\n"

        return ArticleDraft(
            draft_id=f"DFT-{stable_suffix(brief.topic, 10000)}",
            headline=headline,
            subheadline=subheadline,
            hook=hook,
            sections=sections,
            raw_markdown=full_md,
            word_count=len(full_md.split()),
        )

    @staticmethod
    def _strip_fences(text: str) -> str:
        """Remove a wrapping markdown code fence if the model added one."""
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
            stripped = stripped.rsplit("```", 1)[0]
        return stripped.strip()

    @staticmethod
    def _sections_from_markdown(body: str) -> List[NewsletterSection]:
        """Split model output on '## ' headings into typed sections."""
        sections: List[NewsletterSection] = []
        heading: Optional[str] = None
        buffer: List[str] = []

        for line in body.split("\n"):
            if line.startswith("## "):
                if heading is not None:
                    sections.append(
                        NewsletterSection(
                            heading=heading, content_markdown="\n".join(buffer).strip()
                        )
                    )
                heading = line[3:].strip()
                buffer = []
            elif heading is not None:
                buffer.append(line)

        if heading is not None:
            sections.append(
                NewsletterSection(heading=heading, content_markdown="\n".join(buffer).strip())
            )
        return sections

    # -- template path -----------------------------------------------------

    @staticmethod
    def _elaboration_depth(target_word_count: int, finding_count: int) -> int:
        """Elaboration sentences per section, from the brief's length target.

        Capped by `ELABORATION`. A template writer cannot honestly pad to an
        arbitrary target -- it has only the dossier to draw on -- so the Editor
        reports any shortfall rather than the Writer inventing filler.
        """
        if finding_count <= 0:
            return 0
        # Roughly 22 words per elaboration sentence, across all sections.
        wanted = max(1, round(target_word_count / (22 * (finding_count + 1))))
        return min(len(ELABORATION), wanted)

    @staticmethod
    def _source_note(finding: ResearchFinding) -> str:
        """Attribution line derived from the finding's own source."""
        host = urlparse(finding.source_url).netloc.removeprefix("www.")
        return f"The figure is from {host}." if host else "The figure is from the research file."

    @staticmethod
    def _section_for(
        finding: ResearchFinding, depth: int, index: int = 0
    ) -> NewsletterSection:
        # The statistic is copied verbatim so the grounding check can trace it.
        body = [finding.statistic]

        if depth:
            # Lead with the source. It differs per finding, so sections differ
            # by construction rather than by rotating a shared pool -- and it
            # tells the reader where the number came from.
            body.append(WriterAgent._source_note(finding))

        # Rotate the generic pool so consecutive sections do not open with the
        # same sentence. Repetition is invisible to the readability score and
        # obvious to a reader.
        generics = max(0, depth - 1)
        if generics and ELABORATION:
            offset = index % len(ELABORATION)
            rotated = ELABORATION[offset:] + ELABORATION[:offset]
            body.extend(rotated[:generics])

        return NewsletterSection(
            heading=finding.headline,
            content_markdown=" ".join(body),
        )

    @staticmethod
    def _takeaway_section(
        dossier: ResearchDossier, brief: EditorialBrief
    ) -> NewsletterSection:
        lines: List[str] = []
        if dossier.findings:
            # Verbatim quotation, attributable to a dossier finding.
            lines.append(f'> "{dossier.findings[0].verified_quote}"')
            lines.append("")
        if dossier.core_themes:
            themes = ", ".join(dossier.core_themes)
            lines.append(f"The threads running through this edition: {themes}.")
        lines.append(CLOSING[brief.tone])
        return NewsletterSection(
            heading=TAKEAWAY_HEADING,
            content_markdown="\n".join(lines),
        )

    @staticmethod
    def _render(
        headline: str,
        subheadline: str,
        hook: str,
        sections: List[NewsletterSection],
    ) -> str:
        parts = [f"# {headline}", "", f"*{subheadline}*", "", hook, ""]
        for section in sections:
            parts.extend([f"## {section.heading}", "", section.content_markdown, ""])
        return "\n".join(parts).rstrip() + "\n"
