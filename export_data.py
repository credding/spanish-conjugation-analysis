from collections.abc import Hashable

from affix_analysis import VerbAffix, VerbSubject, VerbVariant
from annotated_string import StringAnnotation
from export_model import (
    ExportData,
    ExportElement,
    ExportElementId,
    ExportIrregularity,
    ExportLemma,
    ExportVerb,
    ExportVerbForm,
    ExportVerbFormId,
)
from grammar_model import (
    Element,
    ElementTag,
    Lemma,
    LemmaTag,
    Regularity,
    Verb,
    VerbForm,
)
from regularity_analysis import Irregularity
from spelling_analysis import Homonym
from stress_analysis import Stress
from syllable_analysis import Syllable
from tagged_index import TaggedItem

type TaggedLemma = TaggedItem[LemmaTag, Lemma]
type TaggedElement = TaggedItem[ElementTag, Element]


def build_export_data(
    lemmas: set[TaggedLemma], elements: set[TaggedElement]
) -> ExportData:
    lemmas_sorted = sorted(lemmas, key=lambda x: _lemma_sort(x.value))
    elements_sorted = sorted(elements, key=_element_sort)

    return ExportData(
        lemmas=[_map_lemma_or_verb(x) for x in lemmas_sorted],
        elements=[_map_element_or_verb_form(x) for x in elements_sorted],
    )


def _lemma_sort(lemma: Lemma) -> tuple:
    if isinstance(lemma, Verb):
        return -lemma.freq_adj, lemma.base_form, lemma.part_of_speech
    return -lemma.freq_adj, lemma.base_form, lemma.part_of_speech


def _element_sort(tagged_element: TaggedElement) -> tuple:
    element = tagged_element.value
    if isinstance(element, VerbForm):
        return (
            *_lemma_sort(element.lemma),
            element.tense,
            element.subject,
            element.variant,
            -(Regularity.CORRECT_FORM in tagged_element.tags),
            -(Regularity.REGULAR_MORPHOLOGY in tagged_element.tags),
            -(Regularity.REGULAR_CONSTRUCTION in tagged_element.tags),
            element.preference,
            element.form,
        )
    return *_lemma_sort(element.lemma), element.form


def _map_lemma_or_verb(tagged_lemma: TaggedLemma) -> ExportLemma:
    lemma = tagged_lemma.value
    if isinstance(lemma, Verb):
        return _map_verb(tagged_lemma, lemma)
    return _map_lemma(lemma)


def _map_lemma(lemma: Lemma) -> ExportLemma:
    return ExportLemma(
        part_of_speech=lemma.part_of_speech,
        lemma=lemma.base_form,
        dle_url=lemma.dle_url,
        freq_adj=lemma.freq_adj,
    )


def _map_verb(tagged_lemma: TaggedLemma, verb: Verb) -> ExportVerb:
    return ExportVerb(
        **dict(_map_lemma(verb)),
        regularity=sorted(tagged_lemma.get_tags(Regularity)),
        models=[x.base_form for x in verb.models],
        study_order=verb.study_order,
    )


def _map_element_or_verb_form_id(element: Element) -> ExportElementId:
    if isinstance(element, VerbForm):
        return _map_verb_form_id(element)
    return _map_element_id(element)


def _map_element_id(element: Element) -> ExportElementId:
    return ExportElementId(
        part_of_speech=element.part_of_speech,
        lemma=element.lemma.base_form,
        form=element.form,
    )


def _map_verb_form_id(form: VerbForm) -> ExportVerbFormId:
    return ExportVerbFormId(
        **dict(_map_element_id(form)), tense=form.tense, subject=form.subject
    )


def _map_element_or_verb_form(tagged_element: TaggedElement) -> ExportElement:
    element = tagged_element.value
    if isinstance(element, VerbForm):
        return _map_verb_form(tagged_element, element)
    return _map_element(tagged_element, element)


def _map_element(tagged_element: TaggedElement, element: Element) -> ExportElement:
    return ExportElement(
        **dict(_map_element_id(element)),
        syllables=_map_syllables(element),
        stress_pos=_map_stress_position(element),
        shared_forms=_map_related_elements(tagged_element, Homonym.SHARED_FORM),
        homographs=_map_related_elements(tagged_element, Homonym.HOMOGRAPH),
        homophones=_map_related_elements(tagged_element, Homonym.HOMOPHONE),
        heteronyms=_map_related_elements(tagged_element, Homonym.HETERONYM),
        paronyms=_map_related_elements(tagged_element, Homonym.PARONYM),
    )


def _map_verb_form(tagged_element: TaggedElement, form: VerbForm) -> ExportVerbForm:
    return ExportVerbForm(
        **{**dict(_map_verb_form_id(form)), **dict(_map_element(tagged_element, form))},
        subject_group=sorted(form.subject_group),
        variant=form.variant,
        preference=form.preference,
        affix_range=_map_annotation_range(form, VerbAffix),
        subject_range=_map_annotation_range_or_none(form, VerbSubject),
        variant_range=_map_annotation_range_or_none(form, VerbVariant),
        regularity=sorted(tagged_element.get_tags(Regularity)),
        regular_form=_map_related_verb_form(
            tagged_element, Regularity.REGULAR_MORPHOLOGY
        ),
        regular_construction=_map_related_verb_form(
            tagged_element, Regularity.REGULAR_CONSTRUCTION
        ),
        irregularities=_map_irregularities(form),
    )


def _map_syllables(element: Element) -> list[int]:
    syllables = element.annotated_form.get_annotations(Syllable)
    return [0, *(s.stop for s in syllables)]


def _map_stress_position(element: Element) -> int:
    syllables = element.annotated_form.get_annotations(Syllable)
    stress = element.annotated_form.get_annotation(Stress)
    stressed_syllable = element.annotated_form.get_annotation(
        Syllable, stress.start, stress.stop
    )
    return syllables.index(stressed_syllable)


def _map_annotation_range(
    element: Element, annotation_type: type[StringAnnotation]
) -> tuple[int, int]:
    annotation = element.annotated_form.get_annotation(annotation_type)
    return annotation.start, annotation.stop


def _map_annotation_range_or_none(
    element: Element, annotation_type: type[StringAnnotation]
) -> tuple[int, int] | None:
    annotation = element.annotated_form.get_annotation_or_none(annotation_type)
    if annotation is None:
        return None
    return annotation.start, annotation.stop


def _map_irregularities(element: Element) -> list[ExportIrregularity]:
    irregularities = element.annotated_form.get_annotations(Irregularity)
    return [
        ExportIrregularity(
            regularity=x.regularity, range=(x.start, x.stop), from_form=x.diff_string
        )
        for x in irregularities
    ]


def _map_related_elements(
    tagged_element: TaggedElement, relation: Hashable
) -> list[ExportElementId]:
    return sorted(
        _map_element_or_verb_form_id(x.value)
        for x in tagged_element.get_related(relation)
    )


def _map_related_verb_form(
    tagged_element: TaggedElement, relation: Hashable
) -> ExportVerbFormId | None:
    related_elements = tagged_element.get_related(relation)
    if len(related_elements) == 0:
        return None
    if len(related_elements) > 1:
        msg = (f"multiple elements related by {relation} found for {tagged_element}",)
        raise ValueError(msg)
    related_form = related_elements.pop().value
    if not isinstance(related_form, VerbForm):
        msg = (f"element related by {relation} is not a verb form: {related_form}",)
        raise TypeError(msg)
    return _map_verb_form_id(related_form)
