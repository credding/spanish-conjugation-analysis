from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from grammar_model import Element, ElementTag, FormTag, Regularity
from phonetic_analysis import (
    STRESSED_VOWELS,
    TRANSLATE_ADD_STRESS,
    TRANSLATE_REMOVE_STRESS,
    Phoneme,
)
from run_context import element_index, lemma_index

if TYPE_CHECKING:
    from collections.abc import Hashable

    from tagged_index import TaggedItem


@dataclass(frozen=True, slots=True)
class PhoneticSpelling:
    text: str


@dataclass(frozen=True, slots=True)
class HeteronymicSpelling:
    text: str


@dataclass(frozen=True, slots=True)
class ParonymicSpelling:
    text: str


class Homonym(Enum):
    HOMONYM = "homónimo"
    SHARED_FORM = "forma compartida"
    HOMOGRAPH = "homógrafo"
    HOMOPHONE = "homófono"
    HETERONYM = "heterónimo"
    PARONYM = "parónimo"


def tag_phonetic_spelling(element_tag: ElementTag) -> None:
    tagged_element = element_index[element_tag]
    phonemes = tagged_element.value.annotated_form.get_annotations(Phoneme)
    tagged_element.tag(
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


def tag_shared_forms(element_tag: ElementTag) -> None:
    tagged_element = element_index[element_tag]
    shared_forms = element_index.lookup(
        element_tag.part_of_speech, element_tag.form_tag
    )
    shared_forms.difference_update(
        element_index.lookup(Regularity.INCORRECT_FORM, element_tag.form_tag),
        element_index.lookup(element_tag.lemma_tag),
    )
    for x in shared_forms:
        tagged_element.relate_to(x, Homonym.SHARED_FORM)


def tag_homonyms_lemmas(element_tag: ElementTag) -> None:
    tagged_element = element_index[element_tag]

    for x in _lookup_homonyms(tagged_element):
        lemma_index[x.key.lemma_tag].tag(Homonym.HOMONYM)


def tag_homonyms(element_tag: ElementTag) -> list[ElementTag]:
    tagged_element = element_index[element_tag]

    all_homonyms = _lookup_homonyms(tagged_element)
    if len(all_homonyms) == 0:
        return []

    lemma_index[element_tag.lemma_tag].tag(Homonym.HOMONYM)
    tagged_element.tag(Homonym.HOMONYM)

    homonyms = set(all_homonyms)
    homonyms -= _relate_homonyms(tagged_element, homonyms, FormTag, Homonym.HOMOGRAPH)
    homonyms -= _relate_homonyms(
        tagged_element, homonyms, PhoneticSpelling, Homonym.HOMOPHONE
    )
    homonyms -= _relate_homonyms(
        tagged_element, homonyms, HeteronymicSpelling, Homonym.HETERONYM
    )
    homonyms -= _relate_homonyms(
        tagged_element, homonyms, ParonymicSpelling, Homonym.PARONYM
    )

    return [x.key for x in all_homonyms]


def _lookup_homonyms(
    tagged_element: TaggedItem[ElementTag, Element],
) -> set[TaggedItem[ElementTag, Element]]:
    element_tag = tagged_element.key
    paronymic_spelling = tagged_element.get_tag(ParonymicSpelling)

    homonyms = element_index.lookup(paronymic_spelling)
    homonyms.difference_update(
        element_index.lookup(Regularity.INCORRECT_FORM, paronymic_spelling),
        element_index.lookup(element_tag.part_of_speech, element_tag.form_tag),
        element_index.lookup(element_tag.lemma_tag),
    )

    return homonyms


def _relate_homonyms(
    tagged_element: TaggedItem[ElementTag, Element],
    homonyms: set[TaggedItem[ElementTag, Element]],
    form_tag_type: type[Hashable],
    homonym_tag: Homonym,
) -> set[TaggedItem[ElementTag, Element]]:
    form_tag = tagged_element.get_tag(form_tag_type)

    matching_forms = homonyms & element_index.lookup(form_tag)
    for x in matching_forms:
        x.tag(Homonym.HOMONYM)
        tagged_element.relate_to(x, homonym_tag)

    return matching_forms
