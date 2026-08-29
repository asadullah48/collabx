"""Deterministic prose transforms used by the Editor -> Writer revision loop.

A revision loop is only worth having if the Writer can actually *act* on the
critique. These are the two levers, chosen because they are the two terms in
the Flesch Reading Ease formula:

    FRE = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

`shorten_sentences` reduces words-per-sentence. `simplify_vocabulary` reduces
syllables-per-word. Everything else in the formula is fixed, so any transform
that raises readability must move one of those two ratios.

Both transforms leave statistics and quoted spans untouched. The grounding
check runs against the revised draft, and a revision that mangled a figure or
reworded a quotation would fail a check the original passed -- turning an
improvement into a regression.
"""
import re
from typing import Dict, List, Tuple

# Clause boundaries where a long sentence can be split without changing meaning.
# Ordered by preference: coordinating conjunctions first (cleanest break), then
# subordinators, then the semicolon.
#
# Each entry is (pattern, replacement_prefix, capitalize_next). The pattern
# captures the first character of the following clause so the split can fix its
# case: dropping ". " in front of a lowercase word yields "agents. the results",
# which is a new sentence that does not start with a capital. Entries whose
# prefix already supplies a sentence opener ("However,", "So") leave the
# captured character alone.
_SPLIT_POINTS: List[Tuple[str, str, bool]] = [
    (r",\s+and\s+(\w)", ". ", True),
    (r",\s+but\s+(\w)", ". However, ", False),
    (r",\s+so\s+(\w)", ". So ", False),
    (r",\s+while\s+(\w)", ". Meanwhile, ", False),
    (r",\s+which\s+(\w)", ". This ", False),
    (r";\s+(\w)", ". ", True),
]

# Long words with shorter everyday equivalents. Deliberately conservative:
# every entry is a genuine synonym in this register, not a rough paraphrase.
VOCABULARY: Dict[str, str] = {
    "utilize": "use",
    "utilizes": "uses",
    "utilizing": "using",
    "leverage": "use",
    "leverages": "uses",
    "leveraging": "using",
    "facilitate": "help",
    "facilitates": "helps",
    "demonstrate": "show",
    "demonstrates": "shows",
    "additionally": "also",
    "furthermore": "also",
    "subsequently": "later",
    "approximately": "about",
    "substantially": "greatly",
    "significantly": "greatly",
    "consequently": "so",
    "nevertheless": "still",
    "numerous": "many",
    "sufficient": "enough",
    "initiate": "start",
    "initiates": "starts",
    "terminate": "end",
    "terminates": "ends",
    "implement": "build",
    "implements": "builds",
    "accelerates": "speeds up",
    "orchestration": "coordination",
    "heterogeneous": "mixed",
    "compounding": "growing",
    "proactively": "early",
    "organizations": "companies",
    "capabilities": "abilities",
    "requirements": "needs",
    "methodology": "method",
    "opportunity": "chance",
    "in order to": "to",
    "prior to": "before",
    "due to the fact that": "because",
    "a majority of": "most",
}

# Spans that must survive a transform unchanged: quoted text and statistics.
_PROTECTED = re.compile(
    r"""(?:
          "[^"]*"
        | [“][^”]*[”]
        | \d[\d,]*(?:\.\d+)?\s*(?:%|[xX]\b|thousand|million|billion|trillion)
        | [$£€]\s?\d[\d,]*(?:\.\d+)?
    )""",
    re.VERBOSE,
)

_WORD_IN_SENTENCE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")


def _protect(text: str) -> Tuple[str, List[str]]:
    """Replace protected spans with placeholders, returning them for restore."""
    saved: List[str] = []

    def stash(match: "re.Match[str]") -> str:
        saved.append(match.group(0))
        return f"\x00{len(saved) - 1}\x00"

    return _PROTECTED.sub(stash, text), saved


def _restore(text: str, saved: List[str]) -> str:
    for index, original in enumerate(saved):
        text = text.replace(f"\x00{index}\x00", original)
    return text


def _sentence_word_count(sentence: str) -> int:
    return len(_WORD_IN_SENTENCE.findall(sentence))


def shorten_sentences(text: str, max_words: int) -> str:
    """Split sentences longer than `max_words` at natural clause boundaries.

    Only over-long lines are touched, and each boundary type fires at most once
    per line. Splitting every boundary at once produces a staccato list of
    fragments that scores better but reads worse -- the metric is a proxy for
    readability, not a replacement for it.
    """
    if max_words <= 0:
        return text

    protected, saved = _protect(text)
    out_lines: List[str] = []

    for line in protected.split("\n"):
        # Headings and blockquotes are single units; splitting them produces a
        # heading followed by an orphaned sentence.
        if not line.strip() or line.lstrip().startswith(("#", ">")):
            out_lines.append(line)
            continue

        rebuilt = line
        for pattern, prefix, capitalize_next in _SPLIT_POINTS:
            if _sentence_word_count(rebuilt) <= max_words:
                break

            def split(match: "re.Match[str]", _p: str = prefix, _c: bool = capitalize_next) -> str:
                following = match.group(1)
                return _p + (following.upper() if _c else following)

            rebuilt = re.sub(pattern, split, rebuilt, count=1)
        out_lines.append(rebuilt)

    return _restore("\n".join(out_lines), saved)


def simplify_vocabulary(text: str) -> str:
    """Swap long words for shorter equivalents from `VOCABULARY`.

    Case-preserving for a leading capital, so a substitution at the start of a
    sentence does not lowercase it.
    """
    protected, saved = _protect(text)

    # Multi-word phrases first: replacing "in order to" -> "to" after single
    # words have been swapped would miss phrases whose parts were rewritten.
    ordered = sorted(VOCABULARY.items(), key=lambda kv: -len(kv[0]))

    for long_form, short_form in ordered:
        pattern = re.compile(rf"\b{re.escape(long_form)}\b", re.IGNORECASE)

        def swap(match: "re.Match[str]", _short: str = short_form) -> str:
            found = match.group(0)
            if found[:1].isupper():
                return _short[:1].upper() + _short[1:]
            return _short

        protected = pattern.sub(swap, protected)

    return _restore(protected, saved)


def apply_revisions(text: str, max_sentence_words: int, simplify: bool) -> str:
    """Run the requested transforms in the order that composes best.

    Vocabulary first: shorter words change sentence word counts, so measuring
    sentence length after the swap avoids splitting a sentence that no longer
    needs it.
    """
    revised = simplify_vocabulary(text) if simplify else text
    return shorten_sentences(revised, max_sentence_words)
