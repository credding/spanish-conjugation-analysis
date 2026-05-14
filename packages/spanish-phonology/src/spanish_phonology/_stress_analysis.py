from collections.abc import Sequence
from dataclasses import dataclass

from annotated_string import AnnotatedString, SingletonStringAnnotation

from ._syllable_analysis import Syllable


@dataclass(repr=False)
class Stress(SingletonStringAnnotation):
    pass


def annotate_stress(word: AnnotatedString) -> Stress | None:
    if len(word.string) == 0:
        return None

    syllables = word.get_annotations(Syllable)
    stressed_syllable = _get_stressed_syllable(syllables)
    stress = Stress(word.string, stressed_syllable.start, stressed_syllable.stop)

    word.add_annotation(stress)
    return stress


def _get_stressed_syllable(word: Sequence[Syllable]) -> Syllable:
    stressed_syllable = next((x for x in reversed(word) if x.has_stress), None)
    return stressed_syllable or _get_normal_stressed_syllable(word)


def _get_normal_stressed_syllable(word: Sequence[Syllable]) -> Syllable:
    if len(word) >= 2 and word[-1].string[-1] in "aeiouns":  # noqa: PLR2004
        return word[-2]
    return word[-1]
