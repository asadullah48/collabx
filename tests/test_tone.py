import pytest

from collabx.core.models import ToneStyle
from collabx.core.tone import (
    TONE_PROFILES,
    long_word_ratio,
    mean_sentence_words,
    profile_for,
    tone_alignment,
    tone_diagnostics,
)

PLAIN = "The team shipped it. The work was slow. Then it was fast. Most teams agree."
DENSE = (
    "Heterogeneous orchestration methodologies substantially facilitate the "
    "compounding operationalization of autonomous organizational capabilities "
    "across multinational enterprise infrastructure modernization programmes."
)


def test_every_tone_has_a_profile():
    # profile_for does a dict lookup; a missing tone would be a KeyError at
    # request time rather than a startup failure.
    for tone in ToneStyle:
        assert profile_for(tone) is TONE_PROFILES[tone]


def test_readability_floors_are_ordered_by_how_accessible_each_voice_should_be():
    def floor(tone):
        return profile_for(tone).readability_floor

    assert floor(ToneStyle.DEEP_DIVE_ANALYST) < floor(ToneStyle.TECH_PIONEER)
    assert floor(ToneStyle.TECH_PIONEER) < floor(ToneStyle.EXECUTIVE_BRIEF)
    assert floor(ToneStyle.EXECUTIVE_BRIEF) < floor(ToneStyle.ENGAGING_STORYTELLER)


def test_floors_sit_in_the_band_the_audience_implies():
    # Flesch 80+ is 6th-grade reading level. The stated audience is "CTOs,
    # Founders & Enterprise Architects", which is the 30-59 band. A single
    # floor of 80 was unreachable for every draft ever produced.
    for profile in TONE_PROFILES.values():
        assert 25.0 <= profile.readability_floor <= 60.0


def test_alignment_is_higher_for_prose_that_fits_the_tone():
    assert tone_alignment(PLAIN, ToneStyle.EXECUTIVE_BRIEF) > tone_alignment(
        DENSE, ToneStyle.EXECUTIVE_BRIEF
    )


def test_the_same_prose_scores_differently_across_tones():
    # A constant could not do this. Dense prose sits closer to the analyst
    # envelope than to the storyteller envelope.
    assert tone_alignment(DENSE, ToneStyle.DEEP_DIVE_ANALYST) > tone_alignment(
        DENSE, ToneStyle.ENGAGING_STORYTELLER
    )


def test_alignment_stays_within_its_documented_range():
    for tone in ToneStyle:
        for text in (PLAIN, DENSE, "", "One."):
            assert 0.0 <= tone_alignment(text, tone) <= 1.0


def test_empty_text_scores_zero_alignment():
    assert tone_alignment("", ToneStyle.TECH_PIONEER) == 0.0


def test_diagnostics_are_silent_when_the_draft_fits_the_tone():
    assert tone_diagnostics(PLAIN, ToneStyle.DEEP_DIVE_ANALYST) == []


def test_diagnostics_name_the_measured_value_and_the_target():
    notes = tone_diagnostics(DENSE, ToneStyle.ENGAGING_STORYTELLER)
    assert notes, "dense prose should not satisfy the storyteller envelope"
    joined = " ".join(notes)
    assert "Engaging Storyteller" in joined
    # A critique that says only "too long" is not actionable.
    assert any(char.isdigit() for char in joined)


def test_mean_sentence_words_ignores_markdown_notation():
    assert mean_sentence_words("# A heading here") == mean_sentence_words("A heading here")


def test_long_word_ratio_is_a_share_not_a_count():
    assert long_word_ratio("the cat sat on the mat") == 0.0
    assert 0.0 < long_word_ratio(DENSE) <= 1.0


def test_long_word_ratio_of_empty_text_is_zero():
    assert long_word_ratio("") == 0.0
