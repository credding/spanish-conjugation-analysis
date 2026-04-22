from dataclasses import dataclass
from enum import Enum

from element_index import TaggedElement
from phonetic_analysis import (
    STRESSED_VOWELS,
    TRANSLATE_ADD_STRESS,
    TRANSLATE_REMOVE_STRESS,
    Phoneme,
)
from run_context import element_index


@dataclass(frozen=True)
class PhoneticSpelling:
    text: str


@dataclass(frozen=True)
class HeteronymicSpelling:
    text: str


@dataclass(frozen=True)
class ParonymicSpelling:
    text: str


class Homonym(Enum):
    HOMONYM = "homónimo"
    SHARED_FORM = "forma compartida"
    HOMOGRAPH = "homógrafo"
    HOMOPHONE = "homófono"
    HETERONYM = "heterónimo"
    PARONYM = "parónimo"


def tag_phonetic_spelling(element: TaggedElement):
    phonemes = element.annotated_form.get_annotations(Phoneme)
    element.tag(
        PhoneticSpelling("".join(_get_phonetic_spelling(x) for x in phonemes)),
        HeteronymicSpelling("".join(_get_heteronymic_spelling(x) for x in phonemes)),
        ParonymicSpelling("".join(_get_paronymic_spelling(x) for x in phonemes)),
    )


def _get_phonetic_spelling(phoneme: Phoneme) -> str:
    return (
        phoneme.phoneme.translate(TRANSLATE_ADD_STRESS)
        if any(c in STRESSED_VOWELS for c in phoneme.text)
        else phoneme.phoneme
    )


def _get_heteronymic_spelling(phoneme: Phoneme) -> str:
    return phoneme.phoneme.translate(TRANSLATE_REMOVE_STRESS)


def _get_paronymic_spelling(phoneme: Phoneme) -> str:
    return phoneme.phoneme


def tag_homonyms(element: TaggedElement):
    shared_forms = element_index.lookup(element.class_, element.form)
    shared_forms -= element_index.lookup(element.lemma, element.form)
    if shared_forms:
        element.tag(Homonym.SHARED_FORM)

    phonetic_spelling = element.get_tag(PhoneticSpelling)
    heteronymic_spelling = element.get_tag(HeteronymicSpelling)
    paronymic_spelling = element.get_tag(ParonymicSpelling)
    assert phonetic_spelling and heteronymic_spelling and paronymic_spelling

    paronyms = element_index.lookup(paronymic_spelling)
    paronyms -= element_index.lookup(element.class_, paronymic_spelling)

    if paronyms:
        element.tag(Homonym.HOMONYM)

    homographs = paronyms & element_index.lookup(element.form)
    if homographs:
        element.tag(Homonym.HOMOGRAPH)

    paronyms -= homographs
    homophones = paronyms & element_index.lookup(phonetic_spelling)
    if homophones:
        element.tag(Homonym.HOMOPHONE)

    paronyms -= homophones
    heteronyms = paronyms & element_index.lookup(heteronymic_spelling)
    if heteronyms:
        element.tag(Homonym.HETERONYM)

    paronyms -= heteronyms
    if paronyms:
        element.tag(Homonym.PARONYM)
