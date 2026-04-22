import re
from dataclasses import replace

from conjugation import SpellingChange, VerbAffix, VerbConjugator, VerbSubject
from diff_analysis import DiffAnnotation, annotate_diff
from element_index import TaggedElement
from grammar_model import Regularity, VerbForm
from run_context import (
    element_index,
    regular_construction_conjugator,
    regular_form_conjugator,
)
from string_analysis import AnnotatedString


class IrregularForm(DiffAnnotation):
    pass


class IrregularConstruction(DiffAnnotation):
    pass


def tag_correct_form(correct_form: VerbForm) -> TaggedElement[VerbForm]:
    tagged_form = element_index.index_element(correct_form)
    tagged_form.tag(Regularity.CORRECT_FORM)
    if correct_form.variant:
        tagged_form.tag(correct_form.variant)
    return tagged_form


def tag_form_regularity(correct_form: TaggedElement[VerbForm]):
    regular_forms = _tag_regular_forms(
        correct_form,
        regular_form_conjugator,
        Regularity.REGULAR_FORM,
    )

    if Regularity.REGULAR_FORM in correct_form.tags:
        return
    correct_form.tag(Regularity.IRREGULAR_FORM)

    if not regular_forms:
        return
    regular_form = regular_forms[0]

    annotate_diff(IrregularForm, correct_form.annotated_form, regular_form.text)
    _tag_irregular_affix(correct_form, regular_form)
    _tag_irregular_subject(correct_form, regular_form)


def _tag_irregular_affix(
    correct_form: TaggedElement[VerbForm], regular_form: AnnotatedString
):
    regular_affix = regular_form.get_annotation(VerbAffix)
    assert regular_affix

    affix_start_match = re.search(
        "^([iíy])?[aáeéíioó]+[^aáeéiíoó]*", regular_affix.text
    )
    assert affix_start_match

    affix_pattern = (
        "[aáeéiíoó]+[^aáeéiíoó]*" + regular_affix.text[affix_start_match.end() :] + "$"
    )
    if affix_start_match.group(1):
        affix_pattern = "[iíy]?" + affix_pattern

    affix_match = re.search(affix_pattern, correct_form.annotated_form.text)
    assert affix_match

    correct_form.annotated_form.annotate(
        VerbAffix, affix_match.start(), len(correct_form.annotated_form.text)
    )


def _tag_irregular_subject(
    correct_form: TaggedElement[VerbForm], regular_form: AnnotatedString
):
    regular_subject = regular_form.get_annotation(VerbSubject)
    if not regular_subject:
        return

    if correct_form.annotated_form.text.endswith(regular_subject.text):
        subject_start = len(correct_form.annotated_form.text) - len(
            regular_subject.text
        )
    else:
        affix = correct_form.annotated_form.get_annotations(VerbAffix).pop()
        subject_start = affix.start

    correct_form.annotated_form.annotate(
        VerbSubject, subject_start, len(correct_form.annotated_form.text)
    )


def tag_form_construction(correct_form: TaggedElement[VerbForm]):
    regular_constructions = _tag_regular_forms(
        correct_form,
        regular_construction_conjugator,
        Regularity.REGULAR_CONSTRUCTION,
    )

    if not regular_constructions:
        return

    if Regularity.REGULAR_CONSTRUCTION in correct_form.tags:
        return

    correct_form.tag(Regularity.IRREGULAR_CONSTRUCTION)

    regular_construction = next(
        (
            f
            for i, f in enumerate(regular_constructions)
            if i == correct_form.element.preference
        ),
        regular_constructions[0],
    )
    if not regular_construction:
        return

    annotate_diff(
        IrregularConstruction, correct_form.annotated_form, regular_construction.text
    )


def _tag_regular_forms(
    correct_form: TaggedElement[VerbForm],
    regular_conjugator: VerbConjugator,
    regular_tag: Regularity,
) -> list[AnnotatedString]:
    regular_forms = regular_conjugator.conjugate(
        correct_form.element.lemma,
        correct_form.element.tense,
        correct_form.element.subject,
        correct_form.element.variant,
    )

    for i, regular_form in enumerate(regular_forms):
        tagged_form = element_index.index_element(
            replace(
                correct_form.element,
                form=regular_form.text,
                preference=i,
            )
        )
        for annotation in regular_form.annotations:
            tagged_form.annotated_form.add_annotation(annotation)
        tagged_form.tag(regular_tag)
        if regular_form.get_annotation(SpellingChange):
            tagged_form.tag(Regularity.SPELLING_CHANGE)

    return regular_forms
