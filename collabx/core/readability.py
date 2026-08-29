"""Flesch Reading Ease scoring for editorial drafts.

`EditorFeedback.readability_score` is documented as 0-100 where higher is
better, and `EditorialGraph` treats a *low* score as grounds for revision.
That is Flesch Reading Ease, not the Flesch-Kincaid Grade Level (which runs
in the opposite direction and is unbounded above).

    FRE = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)

Markdown is stripped before scoring. Heading markers, emphasis asterisks and
blockquote carets are notation, not prose, and counting `**` as part of a word
inflates the syllable estimate.
"""
import re
from typing import List

# Sentence terminators. Abbreviations are not special-cased: newsletter prose
# uses few of them, and a false split costs a fraction of a point on a score
# whose gate has a several-point margin.
_SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")

# A word is a run of letters, optionally carrying internal apostrophes or
# hyphens ("don't", "state-machine"). Bare numerals are excluded: "3.4x" has no
# stable syllable count and pronunciation varies by reader.
_WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")

_VOWEL_GROUP = re.compile(r"[aeiouy]+")


def strip_markdown(text: str) -> str:
    """Reduce markdown to the prose a reader would actually say aloud."""
    out = text
    out = re.sub(r"^\s{0,3}#{1,6}\s+", "", out, flags=re.MULTILINE)  # headings
    out = re.sub(r"^\s{0,3}>\s?", "", out, flags=re.MULTILINE)       # blockquotes
    out = re.sub(r"^\s{0,3}[-*+]\s+", "", out, flags=re.MULTILINE)   # list bullets
    out = re.sub(r"`{1,3}[^`]*`{1,3}", " ", out)                     # code spans
    out = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", out)             # links, keep label
    out = re.sub(r"[*_]{1,3}", "", out)                              # emphasis markers
    return out


def count_sentences(text: str) -> int:
    """Number of sentences, never less than 1 for non-empty text."""
    stripped = strip_markdown(text).strip()
    if not stripped:
        return 0
    count = len(_SENTENCE_END.findall(stripped))
    # A heading or a fragment with no terminator is still one unit of prose.
    return max(1, count)


def words_of(text: str) -> List[str]:
    """Prose words in `text`, markdown notation removed."""
    return _WORD.findall(strip_markdown(text))


def count_words(text: str) -> int:
    return len(words_of(text))


def _syllables_in_part(part: str) -> int:
    w = re.sub(r"[^a-z]", "", part.lower())
    if not w:
        return 0

    count = len(_VOWEL_GROUP.findall(w))

    # Silent terminal 'e' ("make" = 1, not 2). Excluded endings keep the vowel
    # audible: "table" (-le), "committee" (-ee), "eye" (-ye).
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and count > 1:
        count -= 1

    # No floor here. A consonant-only fragment contributes nothing; flooring it
    # to 1 would make "don't" two syllables. The floor belongs at word level.
    return count


def count_syllables(word: str) -> int:
    """Heuristic syllable count for a single English word.

    Vowel groups, minus a silent trailing 'e', floored at 1. This is the
    standard approximation used by readability tools; it is wrong on some
    words ("queue", "poem") but stable and dependency-free, and FRE averages
    over the whole document.

    Hyphenated compounds are counted part by part. Treating "state-machine" as
    one token collapses "state" and "machine" into a single vowel run and
    strips only one silent 'e', yielding 4 for a 3-syllable compound.

    Apostrophes are *not* split on. Contractions elide rather than add a
    syllable, and dropping the apostrophe gets that right: "they're" reduces to
    "theyre" (one vowel run plus a silent 'e') rather than "they" + "re".
    """
    parts = [p for p in word.split("-") if p]
    if not parts:
        return 0
    return max(1, sum(_syllables_in_part(p) for p in parts))


def count_total_syllables(text: str) -> int:
    return sum(count_syllables(w) for w in words_of(text))


def flesch_reading_ease(text: str) -> float:
    """Flesch Reading Ease for `text`, clamped to the documented 0-100 range.

    The raw formula can exceed 100 (short simple sentences) or go negative
    (long sentences of polysyllables). The model documents a 0-100 field, so
    the score is clamped rather than allowed to leave the range consumers
    were told to expect.
    """
    words = count_words(text)
    sentences = count_sentences(text)
    if words == 0 or sentences == 0:
        return 0.0

    syllables = count_total_syllables(text)
    raw = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return round(max(0.0, min(100.0, raw)), 1)


def sentences_of(text: str) -> List[str]:
    """Split prose into sentences, for per-sentence analysis by other modules."""
    parts = _SENTENCE_END.split(strip_markdown(text))
    return [p.strip() for p in parts if p.strip()]
