import pytest

from collabx.core.readability import flesch_reading_ease
from collabx.core.revision import (
    apply_revisions,
    shorten_sentences,
    simplify_vocabulary,
)


# --- sentence splitting ----------------------------------------------------


def test_a_long_sentence_is_split_at_a_clause_boundary():
    out = shorten_sentences("Teams adopt agents, and the results improve steadily now.", 6)
    assert "Teams adopt agents." in out


def test_a_split_capitalizes_the_new_sentence():
    # Dropping ". " in front of a lowercase word yields "agents. the results",
    # which is a sentence that does not start with a capital.
    out = shorten_sentences("Teams adopt agents, and the results improve steadily now.", 6)
    assert "the results" not in out
    assert "The results" in out


def test_a_connective_split_leaves_the_following_word_alone():
    out = shorten_sentences(
        "Teams adopt agents, but results vary widely across every team surveyed.", 6
    )
    assert "However, results" in out


@pytest.mark.parametrize("marker", ["#", "##", ">"])
def test_headings_and_blockquotes_are_never_split(marker):
    line = f"{marker} A heading, and a clause, which runs long enough to trigger a split"
    assert shorten_sentences(line, 4) == line


def test_a_short_sentence_is_left_untouched():
    text = "Teams adopt agents."
    assert shorten_sentences(text, 20) == text


def test_a_nonpositive_limit_is_a_no_op():
    text = "Teams adopt agents, and the results improve."
    assert shorten_sentences(text, 0) == text


# --- vocabulary ------------------------------------------------------------


def test_long_words_are_swapped_for_shorter_equivalents():
    assert simplify_vocabulary("Teams utilize agents.") == "Teams use agents."


def test_substitution_preserves_a_leading_capital():
    # Lowercasing here would leave a sentence starting in lower case.
    assert simplify_vocabulary("Additionally, teams ship faster.").startswith("Also,")


def test_multi_word_phrases_are_replaced():
    assert "in order to" not in simplify_vocabulary("They met in order to decide.")


def test_substitution_does_not_match_inside_a_longer_word():
    # A bare substring replace would corrupt "reimplementation".
    assert "reimplementation" in simplify_vocabulary("The reimplementation shipped.")


# --- protected spans -------------------------------------------------------


@pytest.mark.parametrize("span", ["78%", "3.4x", "$4.2B", "2.5 million"])
def test_statistics_survive_revision_byte_for_byte(span):
    # Grounding runs against the revised draft. A revision that mangled a
    # figure would fail a check the original passed.
    text = f"Adoption reached {span}, and the trend continued for several quarters."
    assert span in apply_revisions(text, max_sentence_words=5, simplify=True)


def test_quoted_spans_are_not_reworded():
    quote = '"Teams utilize agents in order to ship, and results improve."'
    out = apply_revisions(f"He said {quote} last week.", max_sentence_words=4, simplify=True)
    assert quote in out


# --- composition -----------------------------------------------------------


def test_revision_raises_the_readability_score():
    dense = (
        "Organizations utilize orchestration methodologies in order to "
        "substantially facilitate delivery, and numerous teams demonstrate "
        "significantly improved outcomes across their portfolios."
    )
    assert flesch_reading_ease(apply_revisions(dense, 12, True)) > flesch_reading_ease(dense)


def test_revision_is_idempotent_enough_to_terminate():
    # The loop stops when a round changes nothing, so a second pass at the same
    # limits must not keep producing new text forever.
    text = "Organizations utilize orchestration, and numerous teams demonstrate gains."
    once = apply_revisions(text, 8, True)
    twice = apply_revisions(once, 8, True)
    assert once == twice


def test_simplify_can_be_disabled_independently():
    text = "Teams utilize agents."
    assert "utilize" in apply_revisions(text, max_sentence_words=50, simplify=False)
