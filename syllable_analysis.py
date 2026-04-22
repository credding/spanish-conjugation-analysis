from dataclasses import dataclass
from enum import Enum, auto

from phonetic_analysis import PhonemeKind, Phoneme
from string_analysis import AnnotatedString, StringAnnotation


@dataclass(eq=False, repr=False)
class Syllable(StringAnnotation):
    pass


def annotate_syllables(word: AnnotatedString) -> list[Syllable]:
    """
    Primary reference: [Syllabification Rules for Spanish (University of Pennsylvania; Mena, C.)](https://catalog.ldc.upenn.edu/docs/LDC2019S07/Syllabification_Rules_in_Spanish.pdf)

    Supporting references:
    - [Syllables in Spanish: A detailed guide to Spanish syllabification rules (BaseLang)](https://baselang.com/blog/pronunciation/spanish-syllables/),
    - [Spanish Syllables and Syllabification Rules (SpanishDictionary.com)](https://www.spanishdict.com/guide/spanish-syllables-and-syllabification-rules)

    This implementation yields incorrect syllabification for Spanish words borrowed from Nahuatl ('tl' is not considered as an unbreakable phoneme).
    """
    state = _SyllableAnalysisState()
    for phoneme in word.get_annotations(Phoneme):
        state.evaluate_phoneme(phoneme)
    return state.evaluate_end()


class _SyllablePart(Enum):
    START_CONSONANT = auto()
    END_CONSONANT = auto()
    END_CONSONANT_LABIODENTAL = auto()
    END_CONSONANT_VELAR = auto()
    END_CONSONANT_DENTAL = auto()
    STRONG_VOWEL = auto()
    WEAK_VOWEL = auto()
    STRONG_WEAK_DIPHTHONG = auto()
    WEAK_STRONG_DIPHTHONG = auto()
    WEAK_WEAK_DIPHTHONG = auto()
    TRIPHTHONG = auto()


class _SyllableAnalysisState:
    def __init__(self):
        self._syllables: list[Syllable] = []
        self._syllable_part: _SyllablePart = _SyllablePart.START_CONSONANT
        self._syllable_phonemes: list[Phoneme] = []

    def evaluate_phoneme(self, phoneme: Phoneme):
        match self._syllable_part:
            case _SyllablePart.START_CONSONANT:
                self._evaluate_at_start_consonant(phoneme)
            case _SyllablePart.END_CONSONANT:
                self._evaluate_at_end_consonant(phoneme)
            case (
                _SyllablePart.END_CONSONANT_LABIODENTAL
                | _SyllablePart.END_CONSONANT_VELAR
            ):
                self._evaluate_at_end_consonant_labiodental_velar(phoneme)
            case _SyllablePart.END_CONSONANT_DENTAL:
                self._evaluate_at_end_consonant_dental(phoneme)
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
        if self._syllable_phonemes:
            self._annotate_syllable()
        return self._syllables

    def _evaluate_at_start_consonant(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._syllable_part = _SyllablePart.START_CONSONANT
            case PhonemeKind.STRONG_VOWEL:
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_at_end_consonant(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._annotate_syllable()
                self._syllable_part = _SyllablePart.START_CONSONANT
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable_without_previous_phoneme()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._add_syllable_without_previous_phoneme()
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_at_end_consonant_labiodental_velar(self, phoneme: Phoneme):
        if phoneme.phoneme_kind == PhonemeKind.CONSONANT and phoneme.phoneme in ("l", "r"):
            self._add_syllable_without_previous_phoneme()
            self._syllable_part = _SyllablePart.START_CONSONANT
            return
        else:
            self._evaluate_at_end_consonant(phoneme)

    def _evaluate_at_end_consonant_dental(self, phoneme: Phoneme):
        if phoneme.phoneme_kind == PhonemeKind.CONSONANT and phoneme.phoneme == "r":
            self._add_syllable_without_previous_phoneme()
            self._syllable_part = _SyllablePart.START_CONSONANT
            return
        else:
            self._evaluate_at_end_consonant(phoneme)

    def _evaluate_at_strong_vowel(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant(phoneme)
            case PhonemeKind.STRONG_VOWEL:
                self._annotate_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.STRONG_WEAK_DIPHTHONG

    def _evaluate_at_weak_vowel(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant(phoneme)
            case PhonemeKind.STRONG_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_STRONG_DIPHTHONG
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.WEAK_WEAK_DIPHTHONG

    def _evaluate_at_strong_diphthong(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant(phoneme)
            case PhonemeKind.STRONG_VOWEL:
                self._annotate_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._syllable_part = _SyllablePart.TRIPHTHONG

    def _evaluate_at_weak_diphthong(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant(phoneme)
            case PhonemeKind.STRONG_VOWEL:
                self._add_syllable_without_previous_phoneme()
                self._syllable_part = _SyllablePart.WEAK_STRONG_DIPHTHONG
            case PhonemeKind.WEAK_VOWEL:
                self._add_syllable_without_previous_phoneme()
                self._syllable_part = _SyllablePart.WEAK_WEAK_DIPHTHONG

    def _evaluate_at_triphthong(self, phoneme: Phoneme):
        match phoneme.phoneme_kind:
            case PhonemeKind.CONSONANT:
                self._evaluate_end_consonant(phoneme)
            case PhonemeKind.STRONG_VOWEL:
                self._annotate_syllable()
                self._syllable_part = _SyllablePart.STRONG_VOWEL
            case PhonemeKind.WEAK_VOWEL:
                self._annotate_syllable()
                self._syllable_part = _SyllablePart.WEAK_VOWEL

    def _evaluate_end_consonant(self, phoneme: Phoneme):
        match phoneme.phoneme:
            case "b" | "f" | "p":
                self._syllable_part = _SyllablePart.END_CONSONANT_LABIODENTAL
            case "k" | "g":
                self._syllable_part = _SyllablePart.END_CONSONANT_VELAR
            case "d" | "t":
                self._syllable_part = _SyllablePart.END_CONSONANT_DENTAL
            case _:
                self._syllable_part = _SyllablePart.END_CONSONANT

    def _add_syllable_without_previous_phoneme(self):
        previous_phoneme = self._syllable_phonemes.pop()
        self._annotate_syllable()
        self._syllable_phonemes.append(previous_phoneme)

    def _annotate_syllable(self):
        first_phoneme = self._syllable_phonemes[0]
        last_phoneme = self._syllable_phonemes[-1]
        first_phoneme.string.annotate(Syllable, first_phoneme.start, last_phoneme.stop)
        self._syllable_phonemes.clear()
