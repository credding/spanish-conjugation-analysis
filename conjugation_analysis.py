import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

import diff_analysis
from conjugation import SpellingChange, VerbAffix, VerbConjugator, VerbSubject
from diff_analysis import DiffAnnotation
from grammar_model import Regularity, VerbForm
from run_context import element_index, lemma_index

if TYPE_CHECKING:
    from annotated_string import AnnotatedString


@dataclass(repr=False)
class IrregularForm(DiffAnnotation):
    pass


@dataclass(repr=False)
class IrregularConstruction(DiffAnnotation):
    pass


def index_regular_forms(
    correct_form: VerbForm, regular_conjugator: VerbConjugator, regular_tag: Regularity
) -> None:
    annotated_forms = regular_conjugator.conjugate(
        correct_form.lemma_tag,
        correct_form.tense,
        correct_form.subject,
        correct_form.variant,
    )
    for i, annotated_form in enumerate(annotated_forms):
        tagged_form = element_index.setdefault(
            replace(correct_form.tag, form=annotated_form.text),
            replace(correct_form, form=annotated_form.text, preference=i),
        )
        regular_form = tagged_form.value

        tagged_form.tag(*regular_form.tags, regular_tag)

        for annotation in annotated_form.annotations:
            regular_form.annotated_form.add_annotation(
                replace(annotation, string=regular_form.annotated_form)
            )

        if Regularity.CORRECT_FORM not in tagged_form.tags:
            tagged_form.tag(Regularity.INCORRECT_FORM)

        if annotated_form.get_annotation_or_none(SpellingChange):
            tagged_form.tag(Regularity.SPELLING_CHANGE)


def annotate_irregular_affix(correct_form: VerbForm) -> None:
    regular_form = _get_regular_form(correct_form)
    if regular_form is None:
        return

    _annotate_irregular_affix(correct_form.annotated_form, regular_form.annotated_form)
    _annotate_irregular_subject(
        correct_form.annotated_form, regular_form.annotated_form
    )


def annotate_irregular_form(correct_form: VerbForm) -> None:
    regular_form = _get_regular_form(correct_form)
    if regular_form is None:
        return

    lemma_index[correct_form.lemma_tag].tag(Regularity.IRREGULAR_VERB)
    element_index[correct_form.tag].tag(Regularity.IRREGULAR_FORM)

    diff_analysis.annotate_diff(
        IrregularForm, correct_form.annotated_form, regular_form.form
    )


def _get_regular_form(correct_form: VerbForm) -> VerbForm | None:
    tagged_correct_form = element_index[correct_form.tag]
    if Regularity.REGULAR_FORM in tagged_correct_form.tags:
        return None

    regular_entries = element_index.lookup(
        correct_form.lemma_tag,
        correct_form.tense,
        correct_form.subject,
        *((correct_form.variant,) if correct_form.variant else ()),
        Regularity.REGULAR_FORM,
    )

    assert len(regular_entries) == 1  # noqa: S101
    tagged_regular_form = regular_entries.pop()
    return cast("VerbForm", tagged_regular_form.value)


_I_PATTERN = r"[iíy]?"
_VERB_CONSONANT_PATTERN = r"[aáeéíioó]+[^aáeéiíoó]*"
_AFFIX_START_PATTERN = re.compile(rf"^({_I_PATTERN}){_VERB_CONSONANT_PATTERN}")


def _annotate_irregular_affix(
    correct_form: AnnotatedString, regular_form: AnnotatedString
) -> None:
    regular_affix = regular_form.get_annotation(VerbAffix)

    affix_start_match = _AFFIX_START_PATTERN.search(regular_affix.text)
    assert affix_start_match is not None  # noqa: S101

    affix_pattern = (
        _VERB_CONSONANT_PATTERN + regular_affix.text[affix_start_match.end() :] + "$"
    )
    if affix_start_match.group(1):
        affix_pattern = _I_PATTERN + affix_pattern

    affix_match = re.search(affix_pattern, correct_form.text)
    assert affix_match is not None  # noqa: S101

    correct_form.annotate(VerbAffix, affix_match.start(), len(correct_form.text))


def _annotate_irregular_subject(
    correct_form: AnnotatedString, regular_form: AnnotatedString
) -> None:
    regular_subject = regular_form.get_annotation_or_none(VerbSubject)
    if regular_subject is None:
        return

    if correct_form.text.endswith(regular_subject.text):
        subject_start = len(correct_form.text) - len(regular_subject.text)
    else:
        affix = correct_form.get_annotations(VerbAffix).pop()
        subject_start = affix.start

    correct_form.annotate(VerbSubject, subject_start, len(correct_form.text))


def annotate_irregular_construction(correct_form: VerbForm) -> None:
    regular_construction = _get_regular_construction(correct_form)
    if regular_construction is None:
        return

    element_index[correct_form.tag].tag(Regularity.IRREGULAR_CONSTRUCTION)

    diff_analysis.annotate_diff(
        IrregularConstruction, correct_form.annotated_form, regular_construction.form
    )


def _get_regular_construction(correct_form: VerbForm) -> VerbForm | None:
    tagged_correct_form = element_index[correct_form.tag]
    if Regularity.REGULAR_CONSTRUCTION in tagged_correct_form.tags:
        return None

    regular_entries = sorted(
        element_index.lookup(
            correct_form.lemma_tag,
            correct_form.tense,
            correct_form.subject,
            *((correct_form.variant,) if correct_form.variant else ()),
            Regularity.REGULAR_CONSTRUCTION,
        ),
        key=lambda x: x.value.preference,
    )

    if len(regular_entries) == 0:
        return None

    tagged_regular_form = next(
        (f for i, f in enumerate(regular_entries) if i == correct_form.preference),
        regular_entries[0],
    )

    return cast("VerbForm", tagged_regular_form.value)
