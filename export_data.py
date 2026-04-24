from typing import Any, Literal, overload

from conjugation import SpellingChange, VerbAffix, VerbSubject, VerbVariant
from conjugation_analysis import IrregularConstruction, IrregularForm
from diff_analysis import DiffAnnotation
from element_index import TaggedElement
from export_model import (
    ExportData,
    ExportElement,
    ExportElementId,
    ExportLemma,
    ExportVerbForm,
    ExportVerbFormId,
    FormChange,
)
from grammar_model import Class, Lemma, Regularity, VerbForm
from run_context import element_index
from spelling_analysis import Homonym
from stress_analysis import WordStress
from string_analysis import StringAnnotation
from syllable_analysis import Syllable


def export_verbs_and_homonyms() -> ExportData:
    tagged_elements = set.union(
        element_index.lookup(Class.VERB),
        element_index.lookup(Homonym.HOMONYM),
    )
    lemmas = {x.lemma for x in tagged_elements}

    return ExportData(
        lemmas=[_map_lemma(x) for x in lemmas],
        elements=[_map_element(x) for x in tagged_elements],
    )


def _map_lemma(lemma: Lemma) -> ExportLemma:
    return ExportLemma(class_=lemma.class_, lemma=lemma.base_form, freq_adj=0)


def _map_element_id(tagged_element: TaggedElement) -> ExportElementId:
    if isinstance(tagged_element.element, VerbForm):
        return _map_verb_form_id(tagged_element)

    return ExportElementId(
        class_=tagged_element.class_,
        lemma=tagged_element.lemma.base_form,
        form=tagged_element.element.form,
    )


def _map_verb_form_id(tagged_form: TaggedElement[VerbForm]) -> ExportVerbFormId:
    return ExportVerbFormId(
        class_=tagged_form.class_,
        lemma=tagged_form.lemma.base_form,
        form=tagged_form.element.form,
        tense=tagged_form.element.tense,
        subject=tagged_form.element.subject,
    )


def _map_element(tagged_element: TaggedElement) -> ExportElement:
    if isinstance(tagged_element.element, VerbForm):
        return _map_verb_form(tagged_element)

    return ExportElement(
        id=_map_element_id(tagged_element),
        syllables=_map_syllables(tagged_element),
        stress_pos=_map_stress_position(tagged_element),
        shared_forms=_map_related_elements(tagged_element, Homonym.SHARED_FORM),
        homographs=_map_related_elements(tagged_element, Homonym.HOMOGRAPH),
        homophones=_map_related_elements(tagged_element, Homonym.HOMOPHONE),
        heteronyms=_map_related_elements(tagged_element, Homonym.HETERONYM),
        paronyms=_map_related_elements(tagged_element, Homonym.PARONYM),
    )


def _map_verb_form(tagged_form: TaggedElement[VerbForm]) -> ExportVerbForm:
    return ExportVerbForm(
        id=_map_verb_form_id(tagged_form),
        subject_group=tagged_form.element.subject_group,
        variant=tagged_form.element.variant,
        preference=tagged_form.element.preference,
        syllables=_map_syllables(tagged_form),
        stress_pos=_map_stress_position(tagged_form),
        affix_range=_map_annotation_range(tagged_form, VerbAffix),
        subject_range=_map_annotation_range(
            tagged_form, VerbSubject, raise_if_absent=False
        ),
        variant_range=_map_annotation_range(
            tagged_form, VerbVariant, raise_if_absent=False
        ),
        regularity=list(tagged_form.get_tags(Regularity)),
        regular_form=_map_related_verb_form(tagged_form, Regularity.REGULAR_FORM),
        regular_construction=_map_related_verb_form(
            tagged_form, Regularity.REGULAR_CONSTRUCTION
        ),
        spelling_change=_map_diff_annotation(tagged_form, SpellingChange),
        form_change=_map_diff_annotation(tagged_form, IrregularForm),
        construction_change=_map_diff_annotation(tagged_form, IrregularConstruction),
        shared_forms=_map_related_elements(tagged_form, Homonym.SHARED_FORM),
        homographs=_map_related_elements(tagged_form, Homonym.HOMOGRAPH),
        homophones=_map_related_elements(tagged_form, Homonym.HOMOPHONE),
        heteronyms=_map_related_elements(tagged_form, Homonym.HETERONYM),
        paronyms=_map_related_elements(tagged_form, Homonym.PARONYM),
    )


def _map_syllables(tagged_element: TaggedElement) -> list[int]:
    syllables = tagged_element.annotated_form.get_annotations(Syllable)
    return [0, *(s.stop for s in syllables)]


def _map_stress_position(tagged_element: TaggedElement) -> int:
    syllables = tagged_element.annotated_form.get_annotations(Syllable)
    stress = tagged_element.annotated_form.get_annotation(WordStress)
    stressed_syllable = tagged_element.annotated_form.get_annotation(
        Syllable, stress.start, stress.stop
    )
    return syllables.index(stressed_syllable)


@overload
def _map_annotation_range(
    tagged_element: TaggedElement,
    annotation_type: type[StringAnnotation],
    /,
    raise_if_absent: Literal[True] = True,
) -> tuple[int, int]: ...
@overload
def _map_annotation_range(
    tagged_element: TaggedElement,
    annotation_type: type[StringAnnotation],
    /,
    raise_if_absent: bool = True,
) -> tuple[int, int] | None: ...
def _map_annotation_range(
    tagged_element: TaggedElement,
    annotation_type: type[StringAnnotation],
    /,
    raise_if_absent: bool = True,
) -> tuple[int, int] | None:
    annotation = tagged_element.annotated_form.get_annotation(
        annotation_type, raise_if_absent=raise_if_absent
    )
    if annotation is None:
        return None
    return annotation.start, annotation.stop


def _map_diff_annotation(
    tagged_element: TaggedElement, annotation_type: type[DiffAnnotation]
) -> FormChange | None:
    annotation = tagged_element.annotated_form.get_annotation(
        annotation_type, raise_if_absent=False
    )
    if annotation is None:
        return None
    return FormChange(
        start_offset=annotation.start,
        end_offset=annotation.stop_offset,
        from_form=annotation.from_string,
    )


def _map_related_elements(
    tagged_element: TaggedElement, relation: Any
) -> list[ExportElementId]:
    return [_map_element_id(x) for x in tagged_element.get_related(relation)]


def _map_related_verb_form(
    tagged_element: TaggedElement, relation: Any
) -> ExportVerbFormId | None:
    related_elements = tagged_element.get_related(relation)
    if len(related_elements) == 0:
        return None
    if len(related_elements) > 1:
        raise ValueError(
            f"multiple elements related by {relation} found for {tagged_element}"
        )
    related_element = related_elements.pop()
    if not isinstance(related_element.element, VerbForm):
        raise ValueError(
            f"element related by {relation} is not a verb form: {related_element}"
        )
    return _map_verb_form_id(related_element)
