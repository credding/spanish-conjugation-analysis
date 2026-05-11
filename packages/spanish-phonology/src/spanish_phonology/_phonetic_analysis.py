from dataclasses import dataclass
from enum import Enum, auto

from annotated_string import AnnotatedString, StringAnnotation

from .phonetics import SOFT_VOWELS, STRESSED_VOWELS, STRONG_VOWELS, VOWELS


class PhonemeKind(Enum):
    CONSONANT = auto()
    STRONG_VOWEL = auto()
    WEAK_VOWEL = auto()


@dataclass(repr=False)
class Phoneme(StringAnnotation):
    phoneme_kind: PhonemeKind
    phoneme: str

    @property
    def has_stress(self) -> bool:
        return any(c in STRESSED_VOWELS for c in self.text)

    def __repr__(self) -> str:
        return (
            f"{super().__repr__()[:-1]}, "
            f"phoneme_kind={self.phoneme_kind!r}, "
            f"phoneme={self.phoneme!r})"
        )


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


def annotate_phonemes(word: AnnotatedString) -> list[Phoneme]:
    phonemes: list[Phoneme] = []
    phoneme = annotate_phoneme(word, 0)
    while phoneme:
        phonemes.append(phoneme)
        phoneme = annotate_phoneme(word, phoneme.stop)
    return phonemes


def annotate_phoneme(word: AnnotatedString, pos: int) -> Phoneme | None:
    return _annotate_compound_phoneme(word, pos) or _annotate_simple_phoneme(word, pos)


def _annotate_compound_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    stop = start + 2
    if stop > len(word.string):
        return None

    grapheme = word.string[start:stop]

    if grapheme[0] == "h" and grapheme[1] in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme[1])

    if grapheme in _COMPOUND_CONSONANT_PHONEMES:
        phoneme = _COMPOUND_CONSONANT_PHONEMES[grapheme]
    elif (
        _is_soft_vowel(word.string, start + 2)
        and grapheme in _COMPOUND_HARD_CONSONANT_PHONEMES
    ):
        phoneme = _COMPOUND_HARD_CONSONANT_PHONEMES[grapheme]
    else:
        return None

    return word.annotate(Phoneme, start, stop, PhonemeKind.CONSONANT, phoneme)


def _annotate_simple_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    stop = start + 1
    if stop > len(word.string):
        return None

    grapheme = word.string[start:stop]

    if grapheme in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme)

    if _is_soft_vowel(word.string, start + 1) and grapheme in _SOFT_CONSONANT_PHONEMES:
        phoneme = _SOFT_CONSONANT_PHONEMES[grapheme]
    elif start == 0 and grapheme in _START_SUBSTITUTE_PHONEMES:
        phoneme = _START_SUBSTITUTE_PHONEMES[grapheme]
    else:
        phoneme = _SUBSTITUTE_PHONEMES.get(grapheme, grapheme)

    return word.annotate(Phoneme, start, stop, PhonemeKind.CONSONANT, phoneme)


def _annotate_vowel_phoneme(
    word: AnnotatedString, start: int, stop: int, grapheme: str
) -> Phoneme:
    phoneme_kind = (
        PhonemeKind.STRONG_VOWEL
        if grapheme in STRONG_VOWELS
        else PhonemeKind.WEAK_VOWEL
    )
    phoneme = _SUBSTITUTE_PHONEMES.get(grapheme, grapheme)

    return word.annotate(Phoneme, start, stop, phoneme_kind, phoneme)


def _is_soft_vowel(word: str, pos: int) -> bool:
    if pos + 1 < len(word) and word[pos] == "h" and word[pos + 1] in SOFT_VOWELS:
        return True
    return pos < len(word) and word[pos] in SOFT_VOWELS
