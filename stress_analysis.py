from dataclasses import dataclass

from phonetic_analysis import STRESSED_VOWELS, Phoneme
from string_analysis import AnnotatedString, StringAnnotation
from syllable_analysis import Syllable

_PENULTIMATE_STRESS_TERMINAL_SOUNDS = "aeiouns"


@dataclass(frozen=True, eq=False, repr=False)
class WordStress(StringAnnotation):
    pass


def annotate_stress(word: AnnotatedString) -> WordStress:
    syllables = word.get_annotations(Syllable)
    stressed_syllable = _get_stressed_syllable(syllables)
    return word.annotate(WordStress, stressed_syllable.start, stressed_syllable.stop)


def _get_stressed_syllable(syllables: list[Syllable]) -> Syllable:
    stressed_syllable = next(
        (s for s in reversed(syllables) if any(x in STRESSED_VOWELS for x in s.text)),
        None,
    )
    if stressed_syllable is not None:
        return stressed_syllable

    return _get_normal_stressed_syllable(syllables)


def _get_normal_stressed_syllable(syllables: list[Syllable]) -> Syllable:
    end_syllable = syllables[-1]

    if len(syllables) >= 2:
        end_syllable_sounds = end_syllable.string.get_annotations(
            Phoneme, end_syllable.start, end_syllable.stop
        )
        if end_syllable_sounds[-1].phoneme in _PENULTIMATE_STRESS_TERMINAL_SOUNDS:
            return syllables[-2]

    return end_syllable
