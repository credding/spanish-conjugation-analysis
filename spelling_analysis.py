from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum

from grammar_model import (
    ElementIndex,
    ElementTag,
    FormTag,
    LemmaIndex,
    Regularity,
    TaggedElement,
)
from phonetic_analysis import (
    STRESSED_VOWELS,
    TRANSLATE_ADD_STRESS,
    TRANSLATE_REMOVE_STRESS,
    Phoneme,
)


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


class SpellingAnalyzer:
    def __init__(self, lemma_index: LemmaIndex, element_index: ElementIndex) -> None:
        self._element_index = element_index
        self._lemma_index = lemma_index

    def tag_phonetic_spelling(self, element_tag: ElementTag) -> None:
        tagged_element = self._element_index[element_tag]
        phonemes = tagged_element.value.annotated_form.get_annotations(Phoneme)
        tagged_element.tag(
            PhoneticSpelling("".join(_get_phonetic_spelling(x) for x in phonemes)),
            HeteronymicSpelling(
                "".join(_get_heteronymic_spelling(x) for x in phonemes)
            ),
            ParonymicSpelling("".join(_get_paronymic_spelling(x) for x in phonemes)),
        )

    def tag_homonyms_lemmas(self, element_tag: ElementTag) -> None:
        tagged_element = self._element_index[element_tag]

        for x in self._lookup_homonyms(tagged_element):
            self._lemma_index[x.key.lemma_tag].tag(Homonym.HOMONYM)

    def tag_shared_forms(self, element_tag: ElementTag) -> None:
        tagged_element = self._element_index[element_tag]
        shared_forms = self._element_index.lookup(
            element_tag.part_of_speech, element_tag.form_tag
        )
        shared_forms.difference_update(
            self._element_index.lookup(Regularity.INCORRECT_FORM, element_tag.form_tag),
            self._element_index.lookup(element_tag.lemma_tag),
        )
        for x in shared_forms:
            tagged_element.relate_to(x, Homonym.SHARED_FORM)

    def tag_homonyms(self, element_tag: ElementTag) -> list[ElementTag]:
        tagged_element = self._element_index[element_tag]

        all_homonyms = self._lookup_homonyms(tagged_element)
        if len(all_homonyms) == 0:
            return []

        self._lemma_index[element_tag.lemma_tag].tag(Homonym.HOMONYM)
        tagged_element.tag(Homonym.HOMONYM)

        homonyms = set(all_homonyms)
        homonyms -= self._relate_homonyms(
            tagged_element, homonyms, FormTag, Homonym.HOMOGRAPH
        )
        homonyms -= self._relate_homonyms(
            tagged_element, homonyms, PhoneticSpelling, Homonym.HOMOPHONE
        )
        homonyms -= self._relate_homonyms(
            tagged_element, homonyms, HeteronymicSpelling, Homonym.HETERONYM
        )
        homonyms -= self._relate_homonyms(
            tagged_element, homonyms, ParonymicSpelling, Homonym.PARONYM
        )

        return [x.key for x in all_homonyms]

    def _lookup_homonyms(self, tagged_element: TaggedElement) -> set[TaggedElement]:
        element_tag = tagged_element.key
        paronymic_spelling = tagged_element.get_tag(ParonymicSpelling)

        homonyms = self._element_index.lookup(paronymic_spelling)
        homonyms.difference_update(
            self._element_index.lookup(Regularity.INCORRECT_FORM, paronymic_spelling),
            self._element_index.lookup(
                element_tag.part_of_speech, element_tag.form_tag
            ),
            self._element_index.lookup(element_tag.lemma_tag),
        )

        return homonyms

    def _relate_homonyms(
        self,
        tagged_element: TaggedElement,
        homonyms: set[TaggedElement],
        form_tag_type: type[Hashable],
        homonym_tag: Homonym,
    ) -> set[TaggedElement]:
        form_tag = tagged_element.get_tag(form_tag_type)

        matching_forms = homonyms & self._element_index.lookup(form_tag)
        for x in matching_forms:
            x.tag(Homonym.HOMONYM)
            tagged_element.relate_to(x, homonym_tag)

        return matching_forms


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
