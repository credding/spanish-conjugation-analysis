from dataclasses import dataclass

from annotated_string import AnnotatedString, StringAnnotation
from phonetic_analysis import STRESSED_VOWELS, Phoneme
from syllable_analysis import Syllable

_PENULTIMATE_STRESS_TERMINAL_SOUNDS = "aeiouns"


@dataclass(repr=False)
class Stress(StringAnnotation):
    pass


def annotate_stress(word: AnnotatedString) -> None:
    syllables = word.get_annotations(Syllable)
    if len(syllables) == 0:
        return

    stressed_syllable = _get_stressed_syllable(syllables)
    word.annotate(Stress, stressed_syllable.start, stressed_syllable.stop)


def _get_stressed_syllable(syllables: list[Syllable]) -> Syllable:
    stressed_syllable = next(
        (s for s in reversed(syllables) if any(x in STRESSED_VOWELS for x in s.text)),
        None,
    )

    return stressed_syllable or _get_normal_stressed_syllable(syllables)


def _get_normal_stressed_syllable(syllables: list[Syllable]) -> Syllable:
    end_syllable = syllables[-1]

    if len(syllables) >= 2:  # noqa: PLR2004
        end_syllable_sounds = end_syllable.string.get_annotations(
            Phoneme, end_syllable.start, end_syllable.stop
        )
        if end_syllable_sounds[-1].phoneme in _PENULTIMATE_STRESS_TERMINAL_SOUNDS:
            return syllables[-2]

    return end_syllable
