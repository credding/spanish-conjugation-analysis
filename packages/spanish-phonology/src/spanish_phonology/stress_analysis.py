from dataclasses import dataclass

from annotated_string import AnnotatedString, StringAnnotation

from .syllable_analysis import Syllable


@dataclass(repr=False)
class Stress(StringAnnotation):
    pass


def annotate_stress(word: AnnotatedString) -> Stress | None:
    syllables = word.get_annotations(Syllable)
    if len(syllables) == 0:
        return None

    stressed_syllable = _get_stressed_syllable(word, syllables)
    return word.annotate(Stress, stressed_syllable.start, stressed_syllable.stop)


def _get_stressed_syllable(
    word: AnnotatedString, syllables: list[Syllable]
) -> Syllable:
    stressed_syllable = next((x for x in reversed(syllables) if x.has_stress), None)
    return stressed_syllable or _get_normal_stressed_syllable(word, syllables)


def _get_normal_stressed_syllable(
    word: AnnotatedString, syllables: list[Syllable]
) -> Syllable:
    if len(syllables) >= 2 and word.string[-1] in "aeiouns":  # noqa: PLR2004
        return syllables[-2]
    return syllables[-1]
