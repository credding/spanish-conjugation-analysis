# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from collections.abc import Hashable
from typing import NamedTuple, TypeAlias, TypedDict, cast

from annotated_string import AnnotatedString
from spanish_conjugation import annotate_verb_form_affix
from spanish_grammar import Element, Lemma, PartOfSpeech, Verb, VerbForm
from spanish_phonology import (
    PhoneticForm,
    SpellingType,
    annotate_phonemes,
    annotate_stress,
    annotate_syllables,
    get_phonetic_form,
)
from tagged_index import TaggedIndex, TaggedItem

from .grammar_index_model import (
    IndexElement,
    IndexLemma,
    IndexVerb,
    IndexVerbForm,
    MappedElement,
    MappedLemma,
    MappedVerb,
    MappedVerbForm,
)

TaggedLemma: TypeAlias = TaggedItem[Lemma, MappedLemma]
TaggedVerb: TypeAlias = TaggedItem[Verb, MappedVerb]
TaggedElement: TypeAlias = TaggedItem[Element, MappedElement]
TaggedVerbForm: TypeAlias = TaggedItem[VerbForm, MappedVerbForm]


class GrammarIndex:
    def __init__(self) -> None:
        self.lemmas: TaggedIndex[Lemma, MappedLemma] = TaggedIndex()
        self.elements: TaggedIndex[Element, MappedElement] = TaggedIndex()

    def index_lemma(self, lemma: IndexLemma, /) -> TaggedLemma:
        if lemma.lemma_tag in self.lemmas:
            return self.lemmas[lemma.lemma_tag]

        tagged_lemma = self.lemmas.index(
            lemma.lemma_tag,
            MappedLemma(
                lemma_tag=lemma.lemma_tag,
                dle_url=lemma.dle_url,
                freq_adj=lemma.freq_adj,
            ),
        )

        tagged_lemma.tag(lemma.lemma_tag, lemma.part_of_speech)

        return tagged_lemma

    def index_verb(self, verb: IndexVerb, /) -> TaggedVerb:
        if verb.lemma_tag in self.lemmas:
            return cast("TaggedVerb", self.lemmas[verb.lemma_tag])

        tagged_verb = self.lemmas.index(
            verb.lemma_tag,
            MappedVerb(
                lemma_tag=verb.lemma_tag,
                freq_adj=verb.freq_adj,
                dle_url=verb.dle_url,
                model_verbs=verb.model_verbs,
                study_order=verb.study_order,
            ),
        )

        tagged_verb.tag(verb.lemma_tag, verb.part_of_speech)

        return cast("TaggedVerb", tagged_verb)

    def lookup_lemmas(self, *tags: Hashable) -> set[TaggedLemma]:
        return self.lemmas.lookup(*tags)

    def lookup_verbs(self, *tags: Hashable) -> set[TaggedVerb]:
        result = self.lemmas.lookup(PartOfSpeech.VERB, *tags)
        return cast("set[TaggedVerb]", result)

    def index_element(self, element: IndexElement, /) -> TaggedElement:
        if element.element_tag in self.elements:
            return self.elements[element.element_tag]

        lemma = self.lemmas[element.lemma_tag].value

        annotated_form, phonetic_forms = _analyze_phonetics(element.form)

        tagged_element = self.elements.index(
            element.element_tag,
            MappedElement(
                element_tag=element.element_tag,
                lemma=lemma,
                annotated_form=annotated_form,
                **phonetic_forms,
            ),
        )

        tagged_element.tag(
            element.lemma_tag,
            element.part_of_speech,
            element.element_tag,
            *phonetic_forms.values(),
        )

        return tagged_element

    def index_verb_form(self, form: IndexVerbForm, /) -> TaggedVerbForm:
        if form.element_tag in self.elements:
            return cast("TaggedVerbForm", self.elements[form.element_tag])

        verb = cast("TaggedVerb", self.lemmas[form.lemma_tag])

        annotated_form, phonetic_forms = _analyze_phonetics(form.form)
        annotate_verb_form_affix(annotated_form, form.lemma_tag, form.inflection)

        tagged_form = self.elements.index(
            form.element_tag,
            MappedVerbForm(
                element_tag=form.element_tag,
                lemma=verb.value,
                annotated_form=annotated_form,
                **phonetic_forms,
                preference=form.preference,
                alt_phonology=form.alt_phonology,
            ),
        )

        tagged_form.tag(
            form.lemma_tag,
            form.part_of_speech,
            form.element_tag,
            form.inflection,
            *phonetic_forms.values(),
        )

        return cast("TaggedVerbForm", tagged_form)

    def lookup_elements(self, *tags: Hashable) -> set[TaggedElement]:
        return self.elements.lookup(*tags)

    def lookup_verb_forms(self, *tags: Hashable) -> set[TaggedVerbForm]:
        result = self.elements.lookup(PartOfSpeech.VERB, *tags)
        return cast("set[TaggedVerbForm]", result)


class _PhoneticAnalysisResult(NamedTuple):
    annotated_form: AnnotatedString
    phonetic_forms: _PhoneticForms


class _PhoneticForms(TypedDict):
    graphic_form: PhoneticForm
    graphic_form_no_stress: PhoneticForm
    phonetic_form: PhoneticForm
    phonetic_form_no_stress: PhoneticForm


def _analyze_phonetics(form: str) -> _PhoneticAnalysisResult:
    annotated_form = AnnotatedString(form)

    annotate_phonemes(annotated_form)
    annotate_syllables(annotated_form)
    annotate_stress(annotated_form)

    return _PhoneticAnalysisResult(
        annotated_form=annotated_form,
        phonetic_forms=_PhoneticForms(
            graphic_form=get_phonetic_form(annotated_form, SpellingType.GRAPHIC),
            graphic_form_no_stress=get_phonetic_form(
                annotated_form, SpellingType.GRAPHIC_NO_STRESS
            ),
            phonetic_form=get_phonetic_form(annotated_form, SpellingType.PHONETIC),
            phonetic_form_no_stress=get_phonetic_form(
                annotated_form, SpellingType.PHONETIC_NO_STRESS
            ),
        ),
    )
