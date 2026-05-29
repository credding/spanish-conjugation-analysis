from collections.abc import Hashable

from annotated_string import StringAnnotation
from pydantic import HttpUrl
from spanish_conjugation import VerbAffix, VerbSubject, VerbVariant
from spanish_phonology import Stress, Syllable

from .conjugation_analysis import Irregularity, Regularity
from .export_model import (
    ExportData,
    ExportElement,
    ExportElementId,
    ExportIrregularity,
    ExportLemma,
    ExportVerb,
    ExportVerbForm,
    ExportVerbFormId,
)
from .grammar_index import TaggedElement, TaggedLemma
from .grammar_index_model import MappedElement, MappedLemma, MappedVerb, MappedVerbForm
from .homonymy_analysis import Homonymy


def build_export_data(
    lemmas: set[TaggedLemma], elements: set[TaggedElement]
) -> ExportData:
    lemmas_sorted = sorted(lemmas, key=_lemma_sort)
    elements_sorted = sorted(elements, key=_element_sort)

    return ExportData(
        lemmas=[_map_lemma_or_verb(x) for x in lemmas_sorted],
        elements=[_map_element_or_verb_form(x) for x in elements_sorted],
    )


def _lemma_sort(tagged_lemma: TaggedLemma) -> tuple:
    lemma = tagged_lemma.value
    return -lemma.freq_adj, lemma.base_form, lemma.part_of_speech


def _element_sort(tagged_element: TaggedElement) -> tuple:
    element = tagged_element.value
    if isinstance(element, MappedVerbForm):
        return (
            -element.lemma.freq_adj,
            element.lemma.base_form,
            element.lemma.part_of_speech,
            element.inflection,
            -(Regularity.CORRECT_FORM in tagged_element.tags),
            -(Regularity.REGULAR_MORPHOLOGY in tagged_element.tags),
            -(Regularity.REGULAR_CONSTRUCTION in tagged_element.tags),
            element.preference,
            element.form,
        )
    return (
        -element.lemma.freq_adj,
        element.lemma.base_form,
        element.lemma.part_of_speech,
        element.form,
    )


def _map_lemma_or_verb(tagged_lemma: TaggedLemma) -> ExportLemma:
    lemma = tagged_lemma.value
    if isinstance(lemma, MappedVerb):
        return _map_verb(tagged_lemma, lemma)
    return _map_lemma(lemma)


def _map_lemma(lemma: MappedLemma) -> ExportLemma:
    return ExportLemma(
        part_of_speech=lemma.part_of_speech,
        lemma=lemma.base_form,
        dle_url=HttpUrl(lemma.dle_url),
        freq_adj=lemma.freq_adj,
    )


def _map_verb(tagged_lemma: TaggedLemma, verb: MappedVerb) -> ExportVerb:
    return ExportVerb(
        **dict(_map_lemma(verb)),
        models=[x.base_form for x in verb.model_verbs],
        study_order=verb.study_order,
        regularity=sorted(x for x in tagged_lemma.tags if isinstance(x, Regularity)),
        homonymy=sorted(x for x in tagged_lemma.tags if isinstance(x, Homonymy)),
    )


def _map_element_or_verb_form_id(element: MappedElement) -> ExportElementId:
    if isinstance(element, MappedVerbForm):
        return _map_verb_form_id(element)
    return _map_element_id(element)


def _map_element_id(element: MappedElement) -> ExportElementId:
    return ExportElementId(
        part_of_speech=element.part_of_speech,
        lemma=element.lemma.base_form,
        form=element.form,
    )


def _map_verb_form_id(form: MappedVerbForm) -> ExportVerbFormId:
    return ExportVerbFormId(
        **dict(_map_element_id(form)), tense=form.tense, subject=form.subject
    )


def _map_element_or_verb_form(tagged_element: TaggedElement) -> ExportElement:
    element = tagged_element.value
    if isinstance(element, MappedVerbForm):
        return _map_verb_form(tagged_element, element)
    return _map_element(tagged_element, element)


def _map_element(
    tagged_element: TaggedElement, element: MappedElement
) -> ExportElement:
    return ExportElement(
        **dict(_map_element_id(element)),
        syllables=_map_syllables(element),
        stress_pos=_map_stress_position(element),
        homonymy=sorted(x for x in tagged_element.tags if isinstance(x, Homonymy)),
        heteronymous_forms=_map_related_elements(
            tagged_element, Homonymy.HETERONYMOUS_FORM
        ),
        shared_forms=_map_related_elements(tagged_element, Homonymy.SHARED_FORM),
        homographs=_map_related_elements(tagged_element, Homonymy.HOMOGRAPH),
        homophones=_map_related_elements(tagged_element, Homonymy.HOMOPHONE),
        heteronyms=_map_related_elements(tagged_element, Homonymy.HETERONYM),
        paronyms=_map_related_elements(tagged_element, Homonymy.PARONYM),
    )


def _map_verb_form(
    tagged_element: TaggedElement, form: MappedVerbForm
) -> ExportVerbForm:
    return ExportVerbForm(
        **{**dict(_map_verb_form_id(form)), **dict(_map_element(tagged_element, form))},
        subject_group=sorted(form.subject_group),
        variant=form.variant,
        preference=form.preference,
        affix_range=_map_annotation_range(form, VerbAffix),
        subject_range=_map_annotation_range_or_none(form, VerbSubject),
        variant_range=_map_annotation_range_or_none(form, VerbVariant),
        regularity=sorted(x for x in tagged_element.tags if isinstance(x, Regularity)),
        regular_spelling=_map_related_verb_form(
            tagged_element, Regularity.REGULAR_SPELLING
        ),
        regular_morphology=_map_related_verb_form(
            tagged_element, Regularity.REGULAR_MORPHOLOGY
        ),
        regular_construction=_map_related_verb_form(
            tagged_element, Regularity.REGULAR_CONSTRUCTION
        ),
        irregularities=_map_irregularities(form),
    )


def _map_syllables(element: MappedElement) -> list[int]:
    syllables = element.annotated_form.get_annotations(Syllable)
    return [0, *(x.stop for x in syllables)]


def _map_stress_position(element: MappedElement) -> int:
    stress = element.annotated_form.get_annotations(Stress)
    return stress[0].start


def _map_annotation_range(
    element: MappedElement, annotation_type: type[StringAnnotation]
) -> tuple[int, int]:
    annotations = element.annotated_form.get_annotations(annotation_type)
    return annotations[0].start, annotations[0].stop


def _map_annotation_range_or_none(
    element: MappedElement, annotation_type: type[StringAnnotation]
) -> tuple[int, int] | None:
    annotations = element.annotated_form.get_annotations(annotation_type)
    if len(annotations) == 0:
        return None
    return annotations[0].start, annotations[0].stop


def _map_irregularities(element: MappedElement) -> list[ExportIrregularity]:
    return sorted(
        (
            ExportIrregularity(
                regularity=x.regularity, range=(x.start, x.stop), diff_text=x.diff_text
            )
            for x in element.annotated_form.get_annotations(Irregularity)
        ),
        key=lambda x: x.regularity,
    )


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
    if not isinstance(related_form, MappedVerbForm):
        msg = (f"element related by {relation} is not a verb form: {related_form}",)
        raise TypeError(msg)
    return _map_verb_form_id(related_form)
