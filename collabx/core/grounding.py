"""Grounding checks: does the draft's evidence trace back to the dossier?

`EditorFeedback.fact_check_passed` was the literal `True`. It is now derived
from a comparison between the draft and the `ResearchDossier` the Researcher
produced.

Scope is deliberately narrow: **statistics and quotations only**. Those are the
two claim types checkable by string comparison with no false positives -- a
figure either appears in the dossier or it does not -- and they are exactly
what a generative writer fabricates. Ordinary prose assertions are *not*
checked; verifying "multi-agent systems reduce errors" against a source needs
semantic matching, which belongs with the model-backed work, not here.

The honest summary: this catches invented numbers and invented quotes. It does
not catch a confidently wrong sentence.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from collabx.core.models import ArticleDraft, ResearchDossier

# A statistic is a number carrying a unit or magnitude marker. Bare integers
# are excluded on purpose: section headings ("## 1. The Shift"), years, and
# ordinals are not claims, and treating them as claims would fail every draft
# for reasons that have nothing to do with fabrication.
_STATISTIC = re.compile(
    r"""
    (?:
        [$£€]\s?\d[\d,]*(?:\.\d+)?\s*(?:[KMB]\b|thousand|million|billion|trillion)?
      | \d[\d,]*(?:\.\d+)?\s*%
      | \d[\d,]*(?:\.\d+)?\s*[xX]\b
      | \d[\d,]*(?:\.\d+)?\s*(?:thousand|million|billion|trillion)\b
    )
    """,
    re.VERBOSE,
)

# Double and smart quotes are unambiguous. Single quotes use boundary
# lookarounds so a contraction ("don't ... it's") cannot be read as a quoted
# span: an opening quote must follow whitespace or markup, a closing quote must
# precede whitespace, markup, or punctuation.
_QUOTE_PATTERNS = [
    re.compile(r'"([^"]{10,})"'),
    re.compile(r"[“]([^”]{10,})[”]"),
    re.compile(r"[‘]([^’]{10,})[’]"),
    re.compile(r"(?<=[\s*(\[])'([^']{10,})'(?=[\s*)\].,;:!?]|$)"),
]


@dataclass
class GroundingReport:
    """Outcome of checking one draft against one dossier."""

    supported_statistics: List[str] = field(default_factory=list)
    unsupported_statistics: List[str] = field(default_factory=list)
    supported_quotes: List[str] = field(default_factory=list)
    unsupported_quotes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.unsupported_statistics and not self.unsupported_quotes

    @property
    def checked_count(self) -> int:
        return (
            len(self.supported_statistics)
            + len(self.unsupported_statistics)
            + len(self.supported_quotes)
            + len(self.unsupported_quotes)
        )

    @property
    def supported_count(self) -> int:
        return len(self.supported_statistics) + len(self.supported_quotes)

    def notes(self) -> List[str]:
        """Critique lines describing what was checked and what failed."""
        if self.checked_count == 0:
            return [
                "Fact-check: no statistics or quotations found in the draft, so "
                "nothing could be verified against the dossier."
            ]

        lines = [
            f"Fact-check: {self.supported_count} of {self.checked_count} checkable "
            f"claims trace to the research dossier."
        ]
        for stat in self.unsupported_statistics:
            lines.append(
                f"Unsupported statistic '{stat}' does not appear in any dossier finding."
            )
        for quote in self.unsupported_quotes:
            excerpt = quote if len(quote) <= 60 else quote[:57] + "..."
            lines.append(f"Unsupported quotation '{excerpt}' is not in any dossier finding.")
        return lines


def _normalize(text: str) -> str:
    """Casefold and collapse whitespace so formatting differences do not matter."""
    return re.sub(r"\s+", " ", text).strip().casefold()


def _normalize_number(text: str) -> str:
    """Normalize a statistic for comparison: no spaces, no thousands separators."""
    return re.sub(r"[\s,]", "", text).casefold()


def dossier_corpus(dossier: ResearchDossier) -> str:
    """Every string in the dossier a claim could legitimately come from."""
    parts: List[str] = [dossier.topic, *dossier.core_themes]
    for finding in dossier.findings:
        parts.extend([finding.headline, finding.statistic, finding.verified_quote])
    return " ".join(parts)


def extract_statistics(text: str) -> List[str]:
    """Statistics asserted in `text`, in order, de-duplicated."""
    seen = set()
    out: List[str] = []
    for match in _STATISTIC.finditer(text):
        value = match.group(0).strip()
        key = _normalize_number(value)
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def extract_quotes(text: str) -> List[str]:
    """Quoted spans asserted in `text`, in order, de-duplicated."""
    seen = set()
    out: List[str] = []
    for pattern in _QUOTE_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(1).strip()
            key = _normalize(value)
            if key and key not in seen:
                seen.add(key)
                out.append(value)
    return out


# Function words carry no topic signal, so they are ignored when checking
# whether the research actually addresses the brief.
_STOPWORDS = frozenset(
    """a an and are as at be by for from has have how in into is it its of on or
    that the their there these this to was were what when where which who will
    with your""".split()
)


def topic_terms(topic: str) -> List[str]:
    """Content words from a brief topic, lowercased and de-duplicated."""
    seen = set()
    out: List[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", topic.casefold()):
        if word in _STOPWORDS or word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


def topic_coherence_note(topic: str, dossier: ResearchDossier) -> Optional[str]:
    """Warn when the dossier shares no vocabulary with the brief topic.

    A brief about regional dairy pricing paired with findings about enterprise
    agent swarms is a research failure, not a writing failure, and it is
    invisible to every other check here: the statistics are all faithfully
    copied from the dossier, so grounding passes cleanly. This is a lexical
    overlap test, so it catches only total mismatch -- which is the case that
    matters and the case that occurs when research is a fixture.
    """
    terms = topic_terms(topic)
    if not terms:
        return None

    # The dossier echoes `topic` verbatim in its own `topic` field, so compare
    # against the findings only -- otherwise every dossier matches every brief.
    findings_corpus = _normalize(
        " ".join(
            part
            for finding in dossier.findings
            for part in (finding.headline, finding.statistic, finding.verified_quote)
        )
        + " "
        + " ".join(dossier.core_themes)
    )
    matched = [t for t in terms if t in findings_corpus]
    if matched:
        return None

    return (
        f"Topic drift: no term from the brief topic ('{topic}') appears anywhere "
        f"in the research findings. The dossier may not be about this brief."
    )


def check_grounding(draft: ArticleDraft, dossier: ResearchDossier) -> GroundingReport:
    """Verify the draft's statistics and quotations against the dossier."""
    report = GroundingReport()
    corpus = dossier_corpus(dossier)
    corpus_numeric = _normalize_number(corpus)
    corpus_prose = _normalize(corpus)

    for stat in extract_statistics(draft.raw_markdown):
        if _normalize_number(stat) in corpus_numeric:
            report.supported_statistics.append(stat)
        else:
            report.unsupported_statistics.append(stat)

    for quote in extract_quotes(draft.raw_markdown):
        # Trailing sentence punctuation is a formatting choice, not part of the
        # claim: a quote is grounded whether or not the writer kept the period.
        needle = _normalize(quote).rstrip(".,;:!?")
        if needle and needle in corpus_prose:
            report.supported_quotes.append(quote)
        else:
            report.unsupported_quotes.append(quote)

    return report
