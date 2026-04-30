import re
from dataclasses import dataclass, replace
from typing import cast

from annotated_string import AnnotatedString
from conjugation import SpellingChange, VerbAffix, VerbConjugator, VerbSubject
from diff_analysis import DiffAnnotation, annotate_diff
from grammar_model import ElementIndex, LemmaIndex, Regularity, VerbForm


@dataclass(repr=False)
class IrregularForm(DiffAnnotation):
    pass


@dataclass(repr=False)
class IrregularConstruction(DiffAnnotation):
    pass


class ConjugationAnalyzer:
    def __init__(self, lemma_index: LemmaIndex, element_index: ElementIndex) -> None:
        self._lemma_index = lemma_index
        self._element_index = element_index

    def index_regular_forms(
        self,
        correct_form: VerbForm,
        regular_conjugator: VerbConjugator,
        regular_tag: Regularity,
    ) -> None:
        annotated_forms = regular_conjugator.conjugate(
            correct_form.lemma_tag,
            correct_form.tense,
            correct_form.subject,
            correct_form.variant,
        )
        for i, annotated_form in enumerate(annotated_forms):
            tagged_form = self._element_index.setdefault(
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

    def annotate_irregular_affix(self, correct_form: VerbForm) -> None:
        regular_form = self._get_regular_form(correct_form)
        if regular_form is None:
            return

        _annotate_irregular_affix(
            correct_form.annotated_form, regular_form.annotated_form
        )
        _annotate_irregular_subject(
            correct_form.annotated_form, regular_form.annotated_form
        )

    def annotate_irregular_form(self, correct_form: VerbForm) -> None:
        regular_form = self._get_regular_form(correct_form)
        if regular_form is None:
            return

        self._lemma_index[correct_form.lemma_tag].tag(Regularity.IRREGULAR_VERB)
        self._element_index[correct_form.tag].tag(Regularity.IRREGULAR_FORM)

        annotate_diff(IrregularForm, correct_form.annotated_form, regular_form.form)

    def _get_regular_form(self, correct_form: VerbForm) -> VerbForm | None:
        tagged_correct_form = self._element_index[correct_form.tag]
        if Regularity.REGULAR_FORM in tagged_correct_form.tags:
            return None

        regular_entries = self._element_index.lookup(
            correct_form.lemma_tag,
            correct_form.tense,
            correct_form.subject,
            *((correct_form.variant,) if correct_form.variant else ()),
            Regularity.REGULAR_FORM,
        )

        if len(regular_entries) != 1:
            msg = f"expected 1 regular form, found {len(regular_entries)}"
            raise ValueError(msg)
        tagged_regular_form = regular_entries.pop()
        return cast("VerbForm", tagged_regular_form.value)

    def annotate_irregular_construction(self, correct_form: VerbForm) -> None:
        regular_construction = self._get_regular_construction(correct_form)
        if regular_construction is None:
            return

        self._element_index[correct_form.tag].tag(Regularity.IRREGULAR_CONSTRUCTION)

        annotate_diff(
            IrregularConstruction,
            correct_form.annotated_form,
            regular_construction.form,
        )

    def _get_regular_construction(self, correct_form: VerbForm) -> VerbForm | None:
        tagged_correct_form = self._element_index[correct_form.tag]
        if Regularity.REGULAR_CONSTRUCTION in tagged_correct_form.tags:
            return None

        regular_entries = sorted(
            self._element_index.lookup(
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


_I_PATTERN = r"[iíy]?"
_VERB_CONSONANT_PATTERN = r"[aáeéíioó]+[^aáeéiíoó]*"
_AFFIX_START_PATTERN = re.compile(rf"^({_I_PATTERN}){_VERB_CONSONANT_PATTERN}")


def _annotate_irregular_affix(
    correct_form: AnnotatedString, regular_form: AnnotatedString
) -> None:
    regular_affix = regular_form.get_annotation(VerbAffix)

    affix_start_match = _AFFIX_START_PATTERN.search(regular_affix.text)
    if affix_start_match is None:
        msg = (
            f"expected regular affix to match {_AFFIX_START_PATTERN.pattern}: "
            f"{regular_affix.text}"
        )
        raise ValueError(msg)

    affix_pattern = (
        _VERB_CONSONANT_PATTERN + regular_affix.text[affix_start_match.end() :] + "$"
    )
    if affix_start_match.group(1):
        affix_pattern = _I_PATTERN + affix_pattern

    affix_match = re.search(affix_pattern, correct_form.text)
    if affix_match is None:
        msg = f"expected irregular form to match {affix_pattern}: {correct_form.text}"
        raise ValueError(msg)

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
