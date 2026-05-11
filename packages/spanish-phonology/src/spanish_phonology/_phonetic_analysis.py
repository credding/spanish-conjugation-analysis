from dataclasses import dataclass
from enum import Enum, auto

from annotated_string import AnnotatedString, StringAnnotation

from .phonetics import (
    SOFT_VOWELS,
    STRESSED_VOWELS,
    STRONG_VOWELS,
    TX_ADD_STRESS,
    TX_REMOVE_STRESS,
    VOWELS,
)


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
    phoneme = annotate_first_phoneme(word)
    while phoneme:
        phonemes.append(phoneme)
        phoneme = annotate_next_phoneme(word, phoneme.stop)
    return phonemes


def annotate_first_phoneme(word: AnnotatedString) -> Phoneme | None:
    if word.string == "":
        return None

    first_phoneme = _START_SUBSTITUTE_PHONEMES.get(word.string[0])
    if first_phoneme is not None:
        return word.annotate(Phoneme, 0, 1, PhonemeKind.CONSONANT, first_phoneme)

    return annotate_next_phoneme(word, 0)


def annotate_next_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    stop = start + 2
    if stop > len(word.string):
        return _annotate_simple_phoneme(word, start)

    grapheme = word.string[start:stop]

    if grapheme[0] == "h" and grapheme[1] in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme[1])

    if grapheme in _COMPOUND_CONSONANT_PHONEMES:
        phoneme = _COMPOUND_CONSONANT_PHONEMES[grapheme]
    elif grapheme in _COMPOUND_HARD_CONSONANT_PHONEMES and _is_soft_vowel(
        word.string, start + 2
    ):
        phoneme = _COMPOUND_HARD_CONSONANT_PHONEMES[grapheme]
    else:
        return _annotate_simple_phoneme(word, start)

    return word.annotate(Phoneme, start, stop, PhonemeKind.CONSONANT, phoneme)


def _annotate_simple_phoneme(word: AnnotatedString, start: int) -> Phoneme | None:
    stop = start + 1
    if stop > len(word.string):
        return None

    grapheme = word.string[start:stop]

    if grapheme in VOWELS:
        return _annotate_vowel_phoneme(word, start, stop, grapheme)

    if grapheme in _SOFT_CONSONANT_PHONEMES and _is_soft_vowel(word.string, start + 1):
        phoneme = _SOFT_CONSONANT_PHONEMES[grapheme]
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
    return pos < len(word) and word[pos] in SOFT_VOWELS


class SpellingType(Enum):
    GRAPHIC = auto()
    GRAPHIC_NO_STRESS = auto()
    PHONETIC = auto()
    PHONETIC_NO_STRESS = auto()


@dataclass(frozen=True, slots=True)
class PhoneticForm:
    spelling_type: SpellingType
    form: str


def get_phonetic_form(
    word: AnnotatedString, spelling_type: SpellingType
) -> PhoneticForm:
    form = {
        SpellingType.GRAPHIC: _get_graphic_form,
        SpellingType.GRAPHIC_NO_STRESS: _get_graphic_form_no_stress,
        SpellingType.PHONETIC: _get_phonetic_form,
        SpellingType.PHONETIC_NO_STRESS: _get_phonetic_form_no_stress,
    }[spelling_type](word)

    return PhoneticForm(spelling_type, form)


def _get_graphic_form(word: AnnotatedString) -> str:
    return word.string


def _get_graphic_form_no_stress(word: AnnotatedString) -> str:
    return word.string.translate(TX_REMOVE_STRESS)


def _get_phonetic_form(word: AnnotatedString) -> str:
    return "".join(
        x.phoneme.translate(TX_ADD_STRESS) if x.has_stress else x.phoneme
        for x in word.get_annotations(Phoneme)
    )


def _get_phonetic_form_no_stress(word: AnnotatedString) -> str:
    return "".join(x.phoneme for x in word.get_annotations(Phoneme))
