from collections.abc import Hashable
from dataclasses import replace
from itertools import groupby

from conjugation import (
    RegularConstructionConjugator,
    RegularMorphologyConjugator,
    RegularSpellingConjugator,
    VerbConjugator,
)
from grammar_base_model import VerbFormTag
from grammar_index import ElementIndex, TaggedVerb, TaggedVerbForm
from grammar_index_model import IndexVerbForm
from regularity_analysis import (
    Irregularity,
    Regularity,
    annotate_irregularity,
    eq_phoneme,
    eq_phoneme_text,
    eq_phoneme_text_norm,
)


class ConjugationAnalyzer:
    def __init__(self, element_index: ElementIndex) -> None:
        self._element_index = element_index

        self._reg_spell_conjug = RegularSpellingConjugator()
        self._reg_morph_conjug = RegularMorphologyConjugator()
        self._reg_constr_conjug = RegularConstructionConjugator(self._element_index)

    def index_regular_verb_forms(self, form: TaggedVerbForm) -> int:
        reg_spell_count = self._index_reg_forms(
            form.key, self._reg_spell_conjug, Regularity.REGULAR_SPELLING
        )
        reg_morph_count = self._index_reg_forms(
            form.key, self._reg_morph_conjug, Regularity.REGULAR_MORPHOLOGY
        )
        reg_constr_count = self._index_reg_forms(
            form.key, self._reg_constr_conjug, Regularity.REGULAR_CONSTRUCTION
        )

        if reg_constr_count > 0:
            form.tag(Regularity.CONSTRUCTED_FORM)

        return reg_spell_count + reg_morph_count + reg_constr_count

    def annotate_regular_spelling_change(self, form: TaggedVerbForm) -> None:
        if Regularity.REGULAR_SPELLING not in form.tags:
            reg_spell_form = self._lookup_reg_spell_form(form)
            self._annotate_reg_spell_change(form, reg_spell_form)

        self._tag_irregularities(form)

    def annotate_form_irregularities(self, form: TaggedVerbForm) -> None:
        if Regularity.REGULAR_SPELLING not in form.tags:
            reg_spell_form = self._lookup_reg_spell_form(form)
            form.relate_to(reg_spell_form, Regularity.REGULAR_SPELLING)
            self._annotate_irreg_spell(form, reg_spell_form)
        if Regularity.REGULAR_MORPHOLOGY not in form.tags:
            reg_morph_form = self._lookup_reg_morph_form(form)
            form.relate_to(reg_morph_form, Regularity.REGULAR_MORPHOLOGY)
            self._annotate_irreg_morph(form, reg_morph_form)
        if Regularity.REGULAR_CONSTRUCTION not in form.tags:
            reg_constr_form = self._lookup_reg_constr_form(form)
            if reg_constr_form is not None:
                form.relate_to(reg_constr_form, Regularity.REGULAR_CONSTRUCTION)
                self._annotate_irreg_constr(form, reg_constr_form)

        self._tag_irregularities(form)

        if Regularity.IRREGULAR_SPELLING not in form.tags:
            form.tag(Regularity.REGULAR_SPELLING)

    def tag_verb_regularity(self, verb: TaggedVerb) -> None:
        form_tags = [
            set.union(*(fx.tags for fx in gx))
            for _, gx in groupby(
                sorted(
                    self._element_index.lookup_verb_forms(
                        Regularity.CORRECT_FORM, verb.value.lemma_tag
                    ),
                    key=lambda x: (x.key.tense, x.key.subject, x.key.variant),
                ),
                key=lambda x: (x.key.tense, x.key.subject, x.key.variant),
            )
        ]

        def _tag(regular_tag: Regularity | None, irregular_tag: Hashable) -> None:
            if all(regular_tag in x for x in form_tags):
                verb.tag(regular_tag)
            if any(irregular_tag in x for x in form_tags):
                verb.tag(irregular_tag)

        _tag(Regularity.REGULAR_SPELLING, Regularity.IRREGULAR_SPELLING)
        _tag(Regularity.REGULAR_MORPHOLOGY, Regularity.IRREGULAR_MORPHOLOGY)
        _tag(Regularity.REGULAR_CONSTRUCTION, Regularity.IRREGULAR_CONSTRUCTION)
        _tag(None, Regularity.REGULAR_SPELLING_CHANGE)

    def _index_reg_forms(
        self, form_tag: VerbFormTag, conjugator: VerbConjugator, regularity: Regularity
    ) -> int:
        reg_annotated_forms = conjugator.conjugate(
            form_tag.lemma_tag, form_tag.conjug_tag
        )

        for i, reg_annotated_form in enumerate(reg_annotated_forms):
            reg_form = self._element_index.index_verb_form(
                IndexVerbForm(
                    element_tag=replace(form_tag, form=reg_annotated_form.string),
                    preference=i,
                    alt_phonology=reg_annotated_form,
                )
            )
            reg_form.tag(regularity)

        return len(reg_annotated_forms)

    def _lookup_reg_spell_form(self, form: TaggedVerbForm) -> TaggedVerbForm:
        reg_spell_forms = self._element_index.lookup_verb_forms(
            Regularity.REGULAR_SPELLING, form.value.lemma_tag, form.value.conjug_tag
        ).difference_tags(Regularity.REGULAR_SPELLING_CHANGE)

        if len(reg_spell_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.key}, found: {len(reg_spell_forms)}"
            )
            raise ValueError(msg)

        return reg_spell_forms.pop()

    def _lookup_reg_morph_form(self, form: TaggedVerbForm) -> TaggedVerbForm:
        reg_morph_forms = self._element_index.lookup_verb_forms(
            Regularity.REGULAR_MORPHOLOGY, form.value.lemma_tag, form.value.conjug_tag
        )

        if len(reg_morph_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.key}, found: {len(reg_morph_forms)}"
            )
            raise ValueError(msg)

        return reg_morph_forms.pop()

    def _lookup_reg_constr_form(self, form: TaggedVerbForm) -> TaggedVerbForm | None:
        reg_constr_forms = self._element_index.lookup_verb_forms(
            Regularity.REGULAR_CONSTRUCTION, form.value.lemma_tag, form.value.conjug_tag
        )
        if len(reg_constr_forms) == 0:
            return None
        if any(x.value.form == form.value.form for x in reg_constr_forms):
            return None

        by_preference = dict[int, TaggedVerbForm]()
        for reg_form in reg_constr_forms:
            preference = reg_form.value.preference
            if preference in by_preference:
                msg = f"duplicate regular construction preference: {preference}"
                raise ValueError(msg)
            by_preference[preference] = reg_form

        return by_preference.get(form.value.preference, by_preference[0])

    def _annotate_reg_spell_change(
        self, form: TaggedVerbForm, reg_spell_form: TaggedVerbForm
    ) -> None:
        annotate_irregularity(
            form.value.annotated_form,
            reg_spell_form.value.alt_phonology or reg_spell_form.value.annotated_form,
            eq=eq_phoneme_text,
            tag=Regularity.REGULAR_SPELLING_CHANGE,
        )

    def _annotate_irreg_spell(
        self, form: TaggedVerbForm, reg_spell_form: TaggedVerbForm
    ) -> None:
        irreg_spell = annotate_irregularity(
            form.value.annotated_form,
            reg_spell_form.value.alt_phonology or reg_spell_form.value.annotated_form,
            eq=eq_phoneme_text_norm,
            tag=Regularity.IRREGULAR_SPELLING,
        )

        if irreg_spell is None:
            self._annotate_reg_spell_change(form, reg_spell_form)

    def _annotate_irreg_morph(
        self, form: TaggedVerbForm, reg_morph_form: TaggedVerbForm
    ) -> None:
        irreg_morph = annotate_irregularity(
            form.value.annotated_form,
            reg_morph_form.value.annotated_form,
            eq=eq_phoneme,
            tag=Regularity.IRREGULAR_MORPHOLOGY,
        )

        if irreg_morph is None:
            return

        reg_suffix = reg_morph_form.value.annotated_form[irreg_morph.diff_stop :]
        reg_spell_change = next(
            (
                x
                for x in reg_suffix.get_annotations(Irregularity)
                if x.regularity is Regularity.REGULAR_SPELLING_CHANGE
            ),
            None,
        )

        if reg_spell_change is not None:
            form.value.annotated_form.add_annotation(
                replace(
                    reg_spell_change,
                    string=form.value.form,
                    start=irreg_morph.stop + reg_spell_change.start,
                    stop=irreg_morph.stop + reg_spell_change.stop,
                )
            )

    def _annotate_irreg_constr(
        self, form: TaggedVerbForm, reg_constr_form: TaggedVerbForm
    ) -> None:
        annotate_irregularity(
            form.value.annotated_form,
            reg_constr_form.value.annotated_form,
            eq=eq_phoneme_text,
            tag=Regularity.IRREGULAR_CONSTRUCTION,
        )

    def _tag_irregularities(self, form: TaggedVerbForm) -> None:
        for x in form.value.annotated_form.get_annotations(Irregularity):
            form.tag(x.regularity)
