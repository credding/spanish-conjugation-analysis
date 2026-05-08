from collections.abc import Hashable
from typing import NamedTuple, TypedDict, cast, overload

from affix_analysis import annotate_verb_form_affix
from annotated_string import AnnotatedString
from grammar_base_model import ElementTag, LemmaTag, PartOfSpeech, VerbFormTag, VerbTag
from grammar_index_model import (
    IndexElement,
    IndexLemma,
    IndexVerb,
    IndexVerbForm,
    MappedElement,
    MappedLemma,
    MappedVerb,
    MappedVerbForm,
)
from phonetic_analysis import (
    PhoneticForm,
    annotate_phonemes,
    get_graphic_form,
    get_graphic_form_no_stress,
    get_phonetic_form,
    get_phonetic_form_no_stress,
)
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables
from tagged_index import ResultSet, TaggedIndex, TaggedItem

type TaggedLemma = TaggedItem[LemmaTag, MappedLemma]
type TaggedVerb = TaggedItem[VerbTag, MappedVerb]
type TaggedElement = TaggedItem[ElementTag, MappedElement]
type TaggedVerbForm = TaggedItem[VerbFormTag, MappedVerbForm]


class LemmaIndex(TaggedIndex[LemmaTag, MappedLemma]):
    @overload
    def __getitem__(self, key: VerbTag) -> TaggedVerb: ...
    @overload
    def __getitem__(self, key: LemmaTag) -> TaggedLemma: ...
    def __getitem__(self, key):
        return super().__getitem__(key)

    def index_lemma(self, lemma: IndexLemma, /) -> TaggedLemma:
        if lemma.lemma_tag in self:
            return self[lemma.lemma_tag]

        tagged_lemma = self.index(
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
        if verb.lemma_tag in self:
            return self[verb.lemma_tag]

        tagged_verb = self.index(
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

    def lookup_verbs(self, *tags: Hashable) -> ResultSet[TaggedVerb]:
        result = self.lookup(PartOfSpeech.VERB, *tags)
        return cast("ResultSet[TaggedVerb]", result)


class ElementIndex(TaggedIndex[ElementTag, MappedElement]):
    def __init__(self, lemma_index: LemmaIndex) -> None:
        super().__init__()
        self._lemma_index = lemma_index

    @overload
    def __getitem__(self, key: VerbFormTag) -> TaggedVerbForm: ...
    @overload
    def __getitem__(self, key: ElementTag) -> TaggedElement: ...
    def __getitem__(self, key):
        return super().__getitem__(key)

    def index_element(self, element: IndexElement, /) -> TaggedElement:
        if element.element_tag in self:
            return self[element.element_tag]

        lemma = self._lemma_index[element.lemma_tag].value

        annotated_form, phonetic_forms = _analyze_phonetics(element.form)

        tagged_element = self.index(
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
        if form.element_tag in self:
            return self[form.element_tag]

        verb = self._lemma_index[form.lemma_tag].value

        annotated_form, phonetic_forms = _analyze_phonetics(form.form)
        annotate_verb_form_affix(annotated_form, form.lemma_tag, form.conjug_tag)

        tagged_form = self.index(
            form.element_tag,
            MappedVerbForm(
                element_tag=form.element_tag,
                lemma=verb,
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
            form.conjug_tag,
            *phonetic_forms.values(),
        )

        return cast("TaggedVerbForm", tagged_form)

    def lookup_verb_forms(self, *tags: Hashable) -> ResultSet[TaggedVerbForm]:
        result = self.lookup(*tags).intersection_tags(PartOfSpeech.VERB)
        return cast("ResultSet[TaggedVerbForm]", result)


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
            graphic_form=get_graphic_form(annotated_form),
            graphic_form_no_stress=get_graphic_form_no_stress(annotated_form),
            phonetic_form=get_phonetic_form(annotated_form),
            phonetic_form_no_stress=get_phonetic_form_no_stress(annotated_form),
        ),
    )
