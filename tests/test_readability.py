import pytest

from collabx.core.readability import (
    count_sentences,
    count_syllables,
    count_words,
    flesch_reading_ease,
    sentences_of,
    strip_markdown,
    words_of,
)


@pytest.mark.parametrize(
    "word,expected",
    [
        ("the", 1),
        ("cat", 1),
        ("make", 1),        # silent terminal 'e'
        ("table", 2),       # -le keeps the vowel audible
        ("committee", 3),   # -ee keeps the vowel audible
        ("enterprise", 3),
        ("orchestration", 4),
        ("autonomous", 4),
        ("readability", 5),
        ("agent", 2),
    ],
)
def test_syllable_counts_match_known_values(word, expected):
    assert count_syllables(word) == expected


@pytest.mark.parametrize(
    "word,expected",
    [("don't", 1), ("they're", 1), ("it's", 1), ("o'clock", 2)],
)
def test_contractions_elide_rather_than_add_a_syllable(word, expected):
    # Splitting on the apostrophe would score "don't" as "don" + "t" = 2.
    assert count_syllables(word) == expected


@pytest.mark.parametrize(
    "word,expected",
    [("state-machine", 3), ("human-in-the-loop", 5)],
)
def test_hyphenated_compounds_are_counted_part_by_part(word, expected):
    # As one token, "state-machine" merges into a single vowel run and strips
    # only one silent 'e', scoring 4 for a 3-syllable compound.
    assert count_syllables(word) == expected


def test_syllable_count_is_never_zero_for_a_real_word():
    assert count_syllables("rhythm") >= 1


def test_markdown_notation_is_not_scored_as_prose():
    assert strip_markdown("# Main Title").strip() == "Main Title"
    assert count_words("# Main Title") == count_words("Main Title")


def test_emphasis_markers_do_not_inflate_word_counts():
    assert count_words("**bold** and *italic* text") == count_words("bold and italic text")


def test_links_keep_their_label_and_drop_the_url():
    stripped = strip_markdown("See [the report](https://example.com/a/b) for detail.")
    assert "the report" in stripped
    assert "example.com" not in stripped


def test_flesch_rewards_short_plain_prose_over_dense_prose():
    plain = "The team shipped it. The work was slow. Then it was fast."
    dense = (
        "Heterogeneous orchestration methodologies substantially facilitate the "
        "compounding operationalization of organizational capabilities."
    )
    assert flesch_reading_ease(plain) > flesch_reading_ease(dense)


def test_flesch_stays_inside_the_documented_range():
    # EditorFeedback documents readability_score as 0-100, so the raw formula
    # (which can exceed 100 or go negative) must be clamped.
    trivial = "It is."
    brutal = " ".join(["incomprehensibility"] * 60) + "."
    assert 0.0 <= flesch_reading_ease(trivial) <= 100.0
    assert 0.0 <= flesch_reading_ease(brutal) <= 100.0


def test_empty_text_scores_zero_rather_than_dividing_by_zero():
    assert flesch_reading_ease("") == 0.0
    assert flesch_reading_ease("   \n  ") == 0.0
    assert count_sentences("") == 0


def test_a_fragment_without_a_terminator_still_counts_as_one_sentence():
    assert count_sentences("A headline with no full stop") == 1


def test_sentences_are_split_on_terminators():
    assert sentences_of("One. Two! Three?") == ["One", "Two", "Three"]


def test_words_exclude_bare_numerals():
    # Digits have no stable syllable count -- "3.4" is read differently by
    # different readers -- so they are not scored. The unit letter stays,
    # because it is pronounced: "3.4x" is read "three point four ex".
    assert words_of("growth of 3.4x this year") == ["growth", "of", "x", "this", "year"]
    assert "3" not in " ".join(words_of("growth of 3.4x this year"))
