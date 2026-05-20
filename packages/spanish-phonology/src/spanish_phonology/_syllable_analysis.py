from dataclasses import dataclass
from enum import Enum, auto

from annotated_string import AnnotatedString, StringAnnotation

from ._phonetic_analysis import Phoneme, PhonemeKind
from .phonetics import STRESSED_VOWELS


@dataclass(repr=False)
class Syllable(StringAnnotation):
    @property
    def has_stress(self) -> bool:
        return any(c in STRESSED_VOWELS for c in self.text)


def annotate_syllables(word: AnnotatedString) -> list[Syllable]:
    """
    Primary reference: [Syllabification Rules for Spanish (University of Pennsylvania;
    Mena, C.)](https://catalog.ldc.upenn.edu/docs/LDC2019S07/Syllabification_Rules_in_Spanish.pdf)

    Supporting references:
    - [Syllables in Spanish: A detailed guide to Spanish syllabification rules (BaseLang)](https://baselang.com/blog/pronunciation/spanish-syllables/),
    - [Spanish Syllables and Syllabification Rules (SpanishDictionary.com)](https://www.spanishdict.com/guide/spanish-syllables-and-syllabification-rules)
    """
    state = _SyllableAnalysisState(word)
    for phoneme in word.get_annotations(Phoneme):
        state.evaluate_phoneme(phoneme)
    return state.evaluate_end()


class _SyllablePart(Enum):
    START_CONSONANT = auto()
    END_CONSONANT = auto()
    STRONG_VOWEL = auto()
    WEAK_VOWEL = auto()
    STRONG_WEAK_DIPHTHONG = auto()
    WEAK_STRONG_DIPHTHONG = auto()
    WEAK_WEAK_DIPHTHONG = auto()
    TRIPHTHONG = auto()


class _SyllableAnalysisState:
    def __init__(self, word: AnnotatedString) -> None:
        self._word = word
        self._syllables: list[Syllable] = []
        self._syllable_part: _SyllablePart = _SyllablePart.START_CONSONANT
        self._syllable_phonemes: list[Phoneme] = []
        self._end_consonant_start: int = 0

    def evaluate_phoneme(self, phoneme: Phoneme) -> None:
        match self._syllable_part:
            case _SyllablePart.START_CONSONANT:
                self._evaluate_at_start_consonant(phoneme)
            case _SyllablePart.END_CONSONANT:
                self._evaluate_at_end_consonant(phoneme)
            case _SyllablePart.STRONG_VOWEL:
                self._evaluate_at_strong_vowel(phoneme)
            case _SyllablePart.WEAK_VOWEL:
                self._evaluate_at_weak_vowel(phoneme)
            case _SyllablePart.WEAK_STRONG_DIPHTHONG:
                self._evaluate_at_strong_diphthong(phoneme)
            case (
                _SyllablePart.STRONG_WEAK_DIPHTHONG | _SyllablePart.WEAK_WEAK_DIPHTHONG
            ):
                self._evaluate_at_weak_diphthong(phoneme)
            case _SyllablePart.TRIPHTHONG:
                self._evaluate_at_triphthong(phoneme)

        self._syllable_phonemes.append(phoneme)

    def evaluate_end(self) -> list[Syllable]:
        match self._syllable_phonemes[self._end_consonant_start :]:
            case [Phoneme(phoneme="t"), Phoneme(phoneme="l")]:
                self._add_syllable_without_previous_phonemes(2)
        if len(self._syllable_phonemes) > 0:
            self._add_syllable()
        return self._syllables

    def _evaluate_at_start_consonant(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                pass
            case PhonemeKind.STRONG_VOWEL:
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_at_end_consonant(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                pass
            case PhonemeKind.STRONG_VOWEL:
                self._evaluate_vowel_following_end_consonant()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._evaluate_vowel_following_end_consonant()
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_vowel_following_end_consonant(self) -> None:
        end_consonant_count = len(self._syllable_phonemes) - self._end_consonant_start
        match self._syllable_phonemes[self._end_consonant_start :]:
            case [
                *_,
                Phoneme(phoneme="p" | "b" | "f" | "g" | "k" | "d" | "t"),
                Phoneme(phoneme="r"),
            ] | [
                *_,
                Phoneme(phoneme="p" | "b" | "f" | "g" | "k"),
                Phoneme(phoneme="l"),
            ]:
                self._add_syllable_without_previous_phonemes(2)
            case _ if end_consonant_count >= 3:  # noqa: PLR2004
                self._add_syllable_without_previous_phonemes(end_consonant_count - 2)
            case _:
                self._add_syllable_without_previous_phonemes(1)

    def _evaluate_at_strong_vowel(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant_start()
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.STRONG_WEAK_DIPHTHONG

    def _evaluate_at_weak_vowel(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant_start()
            case PhonemeKind.STRONG_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_STRONG_DIPHTHONG
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_WEAK_DIPHTHONG

    def _evaluate_at_strong_diphthong(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant_start()
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.TRIPHTHONG

    def _evaluate_at_weak_diphthong(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant_start()
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable_without_previous_phonemes(1)
                self._syllable_part = _SyllablePart.WEAK_STRONG_DIPHTHONG
            case PhonemeKind.WEAK_VOWEL:
                self._add_syllable_without_previous_phonemes(1)
                self._syllable_part = _SyllablePart.WEAK_WEAK_DIPHTHONG

    def _evaluate_at_triphthong(self, phoneme: Phoneme) -> None:
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant_start()
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._add_syllable()
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_end_consonant_start(self) -> None:
        self._syllable_part = _SyllablePart.END_CONSONANT
        self._end_consonant_start = len(self._syllable_phonemes)

    def _add_syllable_without_previous_phonemes(self, extra_phoneme_count: int) -> None:
        self._syllable_phonemes, extra_phonemes = (
            self._syllable_phonemes[:-extra_phoneme_count],
            self._syllable_phonemes[-extra_phoneme_count:],
        )
        self._add_syllable()
        self._syllable_phonemes.extend(extra_phonemes)

    def _add_syllable(self) -> None:
        first_phoneme = self._syllable_phonemes[0]
        last_phoneme = self._syllable_phonemes[-1]
        syllable = Syllable(self._word.string, first_phoneme.start, last_phoneme.stop)
        self._word.add_annotation(syllable)
        self._syllables.append(syllable)
        self._syllable_phonemes.clear()
