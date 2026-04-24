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
    return phoneme.text.translate(TRANSLATE_REMOVE_STRESS)


def _get_paronymic_spelling(phoneme: Phoneme) -> str:
    return phoneme.phoneme


def tag_homonyms(element: TaggedElement) -> set[TaggedElement]:
    shared_forms = element_index.lookup(element.class_, element.form)
    shared_forms -= element_index.lookup(element.lemma, element.form)
    for x in shared_forms:
        element.relate_to(x, Homonym.SHARED_FORM)

    phonetic_spelling = element.get_tag(PhoneticSpelling)
    heteronymic_spelling = element.get_tag(HeteronymicSpelling)
    paronymic_spelling = element.get_tag(ParonymicSpelling)

    all_homonyms = element_index.lookup(paronymic_spelling)
    all_homonyms -= element_index.lookup(element.class_, paronymic_spelling)

    if len(all_homonyms) == 0:
        return all_homonyms

    element.tag(Homonym.HOMONYM)

    homonyms = set(all_homonyms)

    homographs = homonyms & element_index.lookup(element.form)
    for x in homographs:
        element.relate_to(x, Homonym.HOMONYM, Homonym.HOMOGRAPH)

    homonyms -= homographs
    homophones = homonyms & element_index.lookup(phonetic_spelling)
    for x in homophones:
        element.relate_to(x, Homonym.HOMONYM, Homonym.HOMOPHONE)

    homonyms -= homophones
    heteronyms = homonyms & element_index.lookup(heteronymic_spelling)
    for x in heteronyms:
        element.relate_to(x, Homonym.HOMONYM, Homonym.HETERONYM)

    homonyms -= heteronyms
    for x in homonyms:
        element.relate_to(x, Homonym.PARONYM)

    return all_homonyms
