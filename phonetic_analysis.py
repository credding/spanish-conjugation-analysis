from dataclasses import dataclass
from enum import Enum, auto

from annotated_string import AnnotatedString, StringAnnotation


class PhonemeKind(Enum):
    CONSONANT = auto()
    STRONG_VOWEL = auto()
    WEAK_VOWEL = auto()


@dataclass(repr=False)
class Phoneme(StringAnnotation):
    phoneme_kind: PhonemeKind
    phoneme: str

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self.string.text[: self.start]}"
            f"[{self.text}{f'({self.phoneme})' if self.phoneme != self.text else ''}]"
            f"{self.string.text[self.stop :]})"
        )


VOWELS = "aáeéiíoóuúü"
STRESSED_VOWELS = "áéíóú"
STRONG_VOWELS = "aáeéíoóú"
WEAK_VOWELS = "iuü"
HARD_VOWELS = "aáoóuúü"
SOFT_VOWELS = "eéií"

TRANSLATE_ADD_STRESS = str.maketrans("aeiou", "áéíóú")
TRANSLATE_REMOVE_STRESS = str.maketrans("áéíóú", "aeiou")

_SUBSTITUTE_PHONEMES = {
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "ü": "u",
    "c": "k",
    "j": "x",
    "q": "k",
    "v": "b",
    "z": "s",
}
_START_SUBSTITUTE_PHONEMES = {"r": "rr", "x": "s"}
_SOFT_CONSONANT_PHONEMES = {"c": "s", "g": "x"}
_COMPOUND_CONSONANT_PHONEMES = {"ch": "ch", "ll": "y", "rr": "rr"}
_COMPOUND_HARD_CONSONANT_PHONEMES = {"qu": "k", "gu": "g"}


def annotate_phonemes(word: AnnotatedString):
    phonemes: list[Phoneme] = []

    phoneme = _annotate_first_phoneme(word)
    while phoneme:
        phonemes.append(phoneme)
        phoneme = _annotate_next_phoneme(word, phoneme.stop)


def _annotate_first_phoneme(word: AnnotatedString) -> Phoneme | None:
    if word.text == "":
        return None

    first_phoneme = _START_SUBSTITUTE_PHONEMES.get(word.text[0])
    if first_phoneme is not None:
        return word.annotate(Phoneme, 0, 1, PhonemeKind.CONSONANT, first_phoneme)

    return _annotate_next_phoneme(word, 0)


def _annotate_next_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    return _annotate_next_compound_phoneme(
        word, start
    ) or _annotate_next_simple_phoneme(word, start)


def _annotate_next_compound_phoneme(
    word: AnnotatedString, start: int
) -> Phoneme | None:
    stop = start + 2
    if stop > len(word.text):
        return None

    grapheme = word.text[start:stop]

    if grapheme[0] == "h" and grapheme[1] in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme[1])

    if grapheme in _COMPOUND_CONSONANT_PHONEMES:
        phoneme = _COMPOUND_CONSONANT_PHONEMES[grapheme]
    elif grapheme in _COMPOUND_HARD_CONSONANT_PHONEMES and _is_soft_vowel(
        word.text, start + 2
    ):
        phoneme = _COMPOUND_HARD_CONSONANT_PHONEMES[grapheme]
    else:
        return None

    return word.annotate(Phoneme, start, stop, PhonemeKind.CONSONANT, phoneme)


def _annotate_next_simple_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    stop = start + 1
    if stop > len(word.text):
        return None

    grapheme = word.text[start:stop]

    if grapheme in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme)

    if grapheme in _SOFT_CONSONANT_PHONEMES and _is_soft_vowel(word.text, start + 1):
        phoneme = _SOFT_CONSONANT_PHONEMES[grapheme]
    else:
        phoneme = _SUBSTITUTE_PHONEMES.get(grapheme, grapheme)

    return word.annotate(Phoneme, start, stop, PhonemeKind.CONSONANT, phoneme)


def _annotate_vowel_phoneme(
    word: AnnotatedString, start: int, stop: int, grapheme: str
):
    phoneme_kind = (
        PhonemeKind.STRONG_VOWEL
        if grapheme in STRONG_VOWELS
        else PhonemeKind.WEAK_VOWEL
    )
    phoneme = _SUBSTITUTE_PHONEMES.get(grapheme, grapheme)

    return word.annotate(Phoneme, start, stop, phoneme_kind, phoneme)


def _is_soft_vowel(word: str, pos: int) -> bool:
    return pos < len(word) and word[pos] in SOFT_VOWELS
