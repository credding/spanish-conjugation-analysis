from dataclasses import replace
from typing import cast

from affix_analysis import annotate_affix
from conjugation import (
    RegularConstructionConjugator,
    RegularMorphologyConjugator,
    RegularSpellingConjugator,
    VerbConjugator,
)
from grammar_model import (
    Element,
    ElementTag,
    Lemma,
    LemmaTag,
    Regularity,
    VerbForm,
    VerbFormTag,
)
from phonetic_analysis import annotate_phonemes
from regularity_analysis import (
    Irregularity,
    annotate_irregularity,
    eq_phoneme,
    eq_phoneme_text,
    eq_phoneme_text_norm,
)
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables
from tagged_index import TaggedIndex, TaggedItem

type LemmaIndex = TaggedIndex[LemmaTag, Lemma]
type TaggedLemma = TaggedItem[LemmaTag, Lemma]
type ElementIndex = TaggedIndex[ElementTag, Element]
type TaggedElement = TaggedItem[ElementTag, Element]


class ConjugationAnalyzer:
    def __init__(self, lemma_index: LemmaIndex, element_index: ElementIndex) -> None:
        self._element_index = element_index
        self._lemma_index = lemma_index

        self._regular_spelling_conjugator = RegularSpellingConjugator()
        self._regular_morphology_conjugator = RegularMorphologyConjugator()
        self._regular_construction_conjugator = RegularConstructionConjugator(
            self._element_index
        )

    def index_regular_forms(self, form: VerbForm) -> int:
        tagged_form = self._element_index[form.element_tag]

        regular_spelling_count = self._index_regular_forms(
            form, self._regular_spelling_conjugator, Regularity.REGULAR_SPELLING
        )
        regular_morphology_count = self._index_regular_forms(
            form, self._regular_morphology_conjugator, Regularity.REGULAR_MORPHOLOGY
        )
        regular_construction_count = self._index_regular_forms(
            form,
            self._regular_construction_conjugator,
            Regularity.CONSTRUCTED_FORM,
            Regularity.REGULAR_CONSTRUCTION,
        )

        if regular_construction_count > 0:
            tagged_form.tag(Regularity.CONSTRUCTED_FORM)

        return (
            regular_spelling_count
            + regular_morphology_count
            + regular_construction_count
        )

    def _index_regular_forms(
        self, form: VerbForm, conjugator: VerbConjugator, *regularity: Regularity
    ) -> int:
        regular_form_strings = conjugator.conjugate(
            form.lemma_tag, form.tense, form.subject, form.variant
        )

        for i, regular_form_string in enumerate(regular_form_strings):
            regular_form = replace(
                form,
                form=regular_form_string.string,
                preference=i,
                alt_phonology=regular_form_string,
            )

            if regular_form.element_tag in self._element_index:
                tagged_form = self._element_index[regular_form.element_tag]
            else:
                tagged_form = self._index_verb_form(regular_form)

            tagged_form.tag(*regularity)

            if Regularity.CORRECT_FORM not in tagged_form.tags:
                tagged_form.tag(Regularity.INCORRECT_FORM)

        return len(regular_form_strings)

    def _index_verb_form(self, form: VerbForm) -> TaggedItem[VerbFormTag, VerbForm]:
        tagged_form = self._element_index.index(form.element_tag, form)
        tagged_form.tag(*form.tags)

        annotate_phonemes(form.annotated_form)
        annotate_syllables(form.annotated_form)
        annotate_stress(form.annotated_form)

        annotate_affix(
            form.annotated_form, form.lemma_tag, form.tense, form.subject, form.variant
        )

        return cast("TaggedItem[VerbFormTag, VerbForm]", tagged_form)

    def annotate_regular_spelling_changes(self, form: VerbForm) -> None:
        tagged_form = self._element_index[form.element_tag]

        self._annotate_regular_spelling_change(form)

        irregularities = {
            x.regularity
            for x in tagged_form.value.annotated_form.get_annotations(Irregularity)
        }
        tagged_form.tag(*irregularities)

    def annotate_form_irregularities(self, form: VerbForm) -> None:
        tagged_form = self._element_index[form.element_tag]

        self._annotate_irregular_spelling(form)
        self._annotate_irregular_morphology(form)
        self._annotate_irregular_construction(form)

        irregularities = {
            x.regularity
            for x in tagged_form.value.annotated_form.get_annotations(Irregularity)
        }
        tagged_form.tag(*irregularities)

    def _annotate_regular_spelling_change(self, form: VerbForm) -> None:
        regular_form = self._lookup_regular_spelling_form(form)
        annotate_irregularity(
            form.annotated_form,
            regular_form.alt_phonology or regular_form.annotated_form,
            eq=eq_phoneme_text,
            tag=Regularity.REGULAR_SPELLING_CHANGE,
        )

    def _annotate_irregular_spelling(self, form: VerbForm) -> None:
        regular_form = self._lookup_regular_spelling_form(form)
        annotate_irregularity(
            form.annotated_form,
            regular_form.alt_phonology or regular_form.annotated_form,
            eq=eq_phoneme_text_norm,
            tag=Regularity.IRREGULAR_SPELLING,
        )

    def _annotate_irregular_morphology(self, form: VerbForm) -> None:
        regular_form = self._lookup_regular_morphology_form(form)
        irregular_morphology = annotate_irregularity(
            form.annotated_form,
            regular_form.annotated_form,
            eq=eq_phoneme,
            tag=Regularity.IRREGULAR_MORPHOLOGY,
        )

        if irregular_morphology is None:
            return

        irregularity_stop = irregular_morphology.diff_stop
        irregularity_suffix = regular_form.annotated_form[irregularity_stop:]
        regular_spelling_change = next(
            (
                x
                for x in irregularity_suffix.get_annotations(Irregularity)
                if x.regularity == Regularity.REGULAR_SPELLING_CHANGE
            ),
            None,
        )

        if regular_spelling_change is not None:
            form.annotated_form.add_annotation(
                replace(
                    regular_spelling_change,
                    string=form.form,
                    start=irregular_morphology.stop + regular_spelling_change.start,
                    stop=irregular_morphology.stop + regular_spelling_change.stop,
                )
            )

    def _annotate_irregular_construction(self, form: VerbForm) -> None:
        regular_form = self._lookup_regular_construction_form(form)
        if regular_form is None:
            return

        annotate_irregularity(
            form.annotated_form,
            regular_form.annotated_form,
            eq=eq_phoneme_text,
            tag=Regularity.IRREGULAR_CONSTRUCTION,
        )

    def _lookup_regular_spelling_form(self, form: VerbForm) -> VerbForm:
        regular_spelling_forms = self._lookup_regular_forms(
            form, Regularity.REGULAR_SPELLING
        )
        regular_spelling_forms -= self._lookup_regular_forms(
            form, Regularity.REGULAR_SPELLING_CHANGE
        )

        if len(regular_spelling_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.element_tag}, "
                f"found: {len(regular_spelling_forms)}"
            )
            raise ValueError(msg)

        tagged_form = regular_spelling_forms.pop()
        return tagged_form.value

    def _lookup_regular_morphology_form(self, form: VerbForm) -> VerbForm:
        regular_morphology_forms = self._lookup_regular_forms(
            form, Regularity.REGULAR_MORPHOLOGY
        )

        if len(regular_morphology_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.element_tag}, "
                f"found: {len(regular_morphology_forms)}"
            )
            raise ValueError(msg)

        tagged_form = regular_morphology_forms.pop()
        return tagged_form.value

    def _lookup_regular_construction_form(self, form: VerbForm) -> VerbForm | None:
        regular_construction_forms = self._lookup_regular_forms(
            form, Regularity.REGULAR_CONSTRUCTION
        )
        if len(regular_construction_forms) == 0:
            return None
        if any(x.value.form == form.form for x in regular_construction_forms):
            return None

        by_preference = dict[int, TaggedItem[VerbFormTag, VerbForm]]()
        for tagged_form in regular_construction_forms:
            preference = tagged_form.value.preference
            if preference in by_preference:
                msg = f"duplicate regular construction preference: {preference}"
                raise ValueError(msg)
            by_preference[preference] = tagged_form

        return by_preference.get(form.preference, by_preference[0]).value

    def _lookup_regular_forms(
        self, form: VerbForm, regularity: Regularity
    ) -> set[TaggedItem[VerbFormTag, VerbForm]]:
        result = self._element_index.lookup(
            regularity, form.lemma_tag, form.tense, form.subject, form.variant
        )
        return cast("set[TaggedItem[VerbFormTag, VerbForm]]", result)
