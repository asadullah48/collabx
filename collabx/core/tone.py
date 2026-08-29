"""Per-tone quality targets and tone-alignment scoring.

Two things live here.

**Readability floors.** `EditorialGraph` previously gated every draft at a
single Flesch Reading Ease of 80.0. Measured against real prose that gate is
unreachable: FRE 80-89 is 6th-grade reading level, while the newsletter's own
stated audience is "CTOs, Founders & Enterprise Architects". The shipped
sample draft scores 11.8. A single global floor either fails everything or
means nothing, so the floor is per tone, anchored to the published FRE bands:

    90-100  5th grade          60-69  plain English (8th-9th grade)
    80-89   6th grade          50-59  10th-12th grade
    70-79   7th grade          30-49  college
                                0-29  college graduate / professional

**Tone alignment.** `tone_alignment_score` was the constant 0.94. It is now
derived from two measurable proxies: mean sentence length and the share of
long words. These are proxies, not a judgement of voice -- a draft can score
1.0 and still sound wrong. The critique notes say so rather than implying the
number means more than it does.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from collabx.core.models import ToneStyle
from collabx.core.readability import count_syllables, sentences_of, words_of

# A "long word" for the density proxy. Three or more syllables is the
# conventional cutoff used by Gunning Fog for complex words.
LONG_WORD_SYLLABLES = 3


@dataclass(frozen=True)
class ToneProfile:
    """Measurable targets for one editorial voice."""

    label: str
    readability_floor: float
    target_sentence_words: int
    long_word_ratio_ceiling: float
    guidance: str


TONE_PROFILES: Dict[ToneStyle, ToneProfile] = {
    ToneStyle.EXECUTIVE_BRIEF: ToneProfile(
        label="Executive Brief",
        readability_floor=50.0,
        target_sentence_words=14,
        long_word_ratio_ceiling=0.18,
        guidance="Short declarative sentences. Lead with the decision, not the background.",
    ),
    ToneStyle.ENGAGING_STORYTELLER: ToneProfile(
        label="Engaging Storyteller",
        readability_floor=55.0,
        target_sentence_words=15,
        long_word_ratio_ceiling=0.14,
        guidance="Concrete nouns and plain verbs. Carry the reader with narrative, not terminology.",
    ),
    ToneStyle.TECH_PIONEER: ToneProfile(
        label="Tech Pioneer",
        readability_floor=40.0,
        target_sentence_words=18,
        long_word_ratio_ceiling=0.26,
        guidance="Technical vocabulary is expected, but one idea per sentence.",
    ),
    ToneStyle.DEEP_DIVE_ANALYST: ToneProfile(
        label="Deep Dive Analyst",
        readability_floor=30.0,
        target_sentence_words=24,
        long_word_ratio_ceiling=0.34,
        guidance="Dense analysis is acceptable. Sustained argument matters more than brevity.",
    ),
}


def profile_for(tone: ToneStyle) -> ToneProfile:
    return TONE_PROFILES[tone]


def mean_sentence_words(text: str) -> float:
    sentences = sentences_of(text)
    if not sentences:
        return 0.0
    counts = [len(words_of(s)) for s in sentences]
    counts = [c for c in counts if c]
    if not counts:
        return 0.0
    return sum(counts) / len(counts)


def long_word_ratio(text: str) -> float:
    """Share of words with three or more syllables."""
    words = words_of(text)
    if not words:
        return 0.0
    long_words = sum(1 for w in words if count_syllables(w) >= LONG_WORD_SYLLABLES)
    return long_words / len(words)


def _decay(actual: float, target: float) -> float:
    """1.0 at or under target, decaying to 0.0 at twice the target.

    Linear rather than stepped so the revision loop can see whether an edit
    moved the draft in the right direction, not just whether it crossed a line.
    """
    if target <= 0:
        return 0.0
    if actual <= target:
        return 1.0
    overshoot = (actual - target) / target
    return max(0.0, 1.0 - overshoot)


def tone_alignment(text: str, tone: ToneStyle) -> float:
    """Alignment of `text` with `tone`, in 0.0-1.0.

    The mean of two proxies: sentence length against the tone's target, and
    long-word density against its ceiling. Neither measures voice. A draft
    scoring 1.0 is within this tone's structural envelope, which is a weaker
    claim than "sounds right".
    """
    profile = profile_for(tone)
    if not words_of(text):
        return 0.0

    length_score = _decay(mean_sentence_words(text), profile.target_sentence_words)
    density_score = _decay(long_word_ratio(text), profile.long_word_ratio_ceiling)
    return round((length_score + density_score) / 2, 2)


def tone_diagnostics(text: str, tone: ToneStyle) -> List[str]:
    """Human-readable notes on how `text` misses `tone`, empty when it fits."""
    profile = profile_for(tone)
    notes: List[str] = []

    mean_len = mean_sentence_words(text)
    if mean_len > profile.target_sentence_words:
        notes.append(
            f"Mean sentence length is {mean_len:.1f} words against a "
            f"{profile.target_sentence_words}-word target for "
            f"'{profile.label}'. {profile.guidance}"
        )

    ratio = long_word_ratio(text)
    if ratio > profile.long_word_ratio_ceiling:
        notes.append(
            f"Long words ({LONG_WORD_SYLLABLES}+ syllables) are {ratio:.0%} of the "
            f"draft against a {profile.long_word_ratio_ceiling:.0%} ceiling for "
            f"'{profile.label}'."
        )

    return notes
