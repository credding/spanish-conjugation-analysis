from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass, replace

from annotated_string import AnnotatedString, DiffStringAnnotation
from ordered_enum import OrderedEnum
from spanish_conjugation import (
    RegularMorphologyConjugator,
    RegularSpellingConjugator,
    VerbConjugator,
)
from spanish_grammar import Inflection, Tense, Verb, VerbForm
from spanish_phonology import SpellingType, annotate_phonemes, get_phonetic_diff

from .grammar_index import GrammarIndex, TaggedVerb, TaggedVerbForm
from .grammar_index_model import IndexVerbForm, MappedVerbForm


class Regularity(OrderedEnum):
    MODEL_VERB = "verbo modelo"
    CORRECT_FORM = "forma correcta"
    INCORRECT_FORM = "forma incorrecta"
    CONSTRUCTED_FORM = "forma construida"
    REGULAR_MORPHOLOGY = "morfología regular"
    IRREGULAR_MORPHOLOGY = "morfología irregular"
    REGULAR_SPELLING = "ortografía regular"
    IRREGULAR_SPELLING = "ortografía irregular"
    REGULAR_SPELLING_CHANGE = "cambio ortográfico regular"
    REGULAR_CONSTRUCTION = "construcción regular"
    IRREGULAR_CONSTRUCTION = "construcción irregular"


@dataclass(repr=False)
class Irregularity(DiffStringAnnotation):
    regularity: Regularity

    def unique_key(self) -> Hashable:
        return type(self), self.regularity


class _CorrectBaseFormConjugator(VerbConjugator):
    def __init__(self, index: GrammarIndex) -> None:
        self._index = index

    def conjugate(self, verb: Verb, inflection: Inflection) -> list[AnnotatedString]:
        if inflection.tense is Tense.INFINITIVE:
            return []

        correct_forms = self._index.lookup_verb_forms(
            Regularity.CORRECT_FORM, verb, inflection
        )
        base_forms: list[AnnotatedString] = []
        for form in sorted(correct_forms, key=lambda x: x.value.preference):
            base_form = AnnotatedString(form.value.form)
            annotate_phonemes(base_form)
            base_forms.append(base_form)

        return base_forms


class ConjugationAnalyzer:
    def __init__(self, index: GrammarIndex) -> None:
        self._index = index

        self._reg_spell_conjug = RegularSpellingConjugator()
        self._reg_morph_conjug = RegularMorphologyConjugator()
        self._reg_constr_conjug = RegularMorphologyConjugator(
            _CorrectBaseFormConjugator(self._index)
        )

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
            _annotate_reg_spell_change(form.value, reg_spell_form.value)

        _tag_irregularities(form)

    def annotate_form_irregularities(self, form: TaggedVerbForm) -> None:
        if Regularity.REGULAR_SPELLING not in form.tags:
            reg_spell_form = self._lookup_reg_spell_form(form)
            form.relate_to(reg_spell_form, Regularity.REGULAR_SPELLING)
            _annotate_irreg_spell(form.value, reg_spell_form.value)

        if Regularity.REGULAR_MORPHOLOGY not in form.tags:
            reg_morph_form = self._lookup_reg_morph_form(form)
            form.relate_to(reg_morph_form, Regularity.REGULAR_MORPHOLOGY)
            _annotate_irreg_morph(form.value, reg_morph_form.value)

        if Regularity.REGULAR_CONSTRUCTION not in form.tags:
            reg_constr_form = self._lookup_reg_constr_form(form)
            if reg_constr_form is not None:
                form.relate_to(reg_constr_form, Regularity.REGULAR_CONSTRUCTION)
                _annotate_irreg_constr(form.value, reg_constr_form.value)

        _tag_irregularities(form)

        if Regularity.IRREGULAR_SPELLING not in form.tags:
            form.tag(Regularity.REGULAR_SPELLING)

    def tag_verb_regularity(self, verb: TaggedVerb) -> None:
        correct_form_tags: dict[Inflection, set[Hashable]] = defaultdict(set)
        for form in self._index.lookup_verb_forms(
            Regularity.CORRECT_FORM, verb.value.lemma_tag
        ):
            correct_form_tags[form.value.inflection].update(form.tags)

        def _tag(regular_tag: Regularity | None, irregular_tag: Hashable) -> None:
            if all(regular_tag in x for x in correct_form_tags.values()):
                verb.tag(regular_tag)
            if any(irregular_tag in x for x in correct_form_tags.values()):
                verb.tag(irregular_tag)

        _tag(Regularity.REGULAR_SPELLING, Regularity.IRREGULAR_SPELLING)
        _tag(Regularity.REGULAR_MORPHOLOGY, Regularity.IRREGULAR_MORPHOLOGY)
        _tag(Regularity.REGULAR_CONSTRUCTION, Regularity.IRREGULAR_CONSTRUCTION)
        _tag(None, Regularity.REGULAR_SPELLING_CHANGE)

    def _index_reg_forms(
        self, form_tag: VerbForm, conjugator: VerbConjugator, regularity: Regularity
    ) -> int:
        reg_annotated_forms = conjugator.conjugate(form_tag.lemma, form_tag.inflection)

        for i, reg_annotated_form in enumerate(reg_annotated_forms):
            reg_form = self._index.index_verb_form(
                IndexVerbForm(
                    element_tag=replace(form_tag, form=reg_annotated_form.string),
                    preference=i,
                    alt_phonology=reg_annotated_form,
                )
            )
            reg_form.tag(regularity)

            if Regularity.CORRECT_FORM not in reg_form.tags:
                reg_form.tag(Regularity.INCORRECT_FORM)

        return len(reg_annotated_forms)

    def _lookup_reg_spell_form(self, form: TaggedVerbForm) -> TaggedVerbForm:
        reg_spell_forms = self._index.lookup_verb_forms(
            Regularity.REGULAR_SPELLING, form.value.lemma_tag, form.value.inflection
        )
        reg_spell_forms -= {
            x for x in reg_spell_forms if Regularity.REGULAR_SPELLING_CHANGE in x.tags
        }

        if len(reg_spell_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.key}, found: {len(reg_spell_forms)}"
            )
            raise ValueError(msg)

        return reg_spell_forms.pop()

    def _lookup_reg_morph_form(self, form: TaggedVerbForm) -> TaggedVerbForm:
        reg_morph_forms = self._index.lookup_verb_forms(
            Regularity.REGULAR_MORPHOLOGY, form.value.lemma_tag, form.value.inflection
        )

        if len(reg_morph_forms) != 1:
            msg = (
                f"expected 1 regular form for {form.key}, found: {len(reg_morph_forms)}"
            )
            raise ValueError(msg)

        return reg_morph_forms.pop()

    def _lookup_reg_constr_form(self, form: TaggedVerbForm) -> TaggedVerbForm | None:
        reg_constr_forms = self._index.lookup_verb_forms(
            Regularity.REGULAR_CONSTRUCTION, form.value.lemma_tag, form.value.inflection
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
    form: MappedVerbForm, reg_spell_form: MappedVerbForm
) -> None:
    _annotate_irregularity(
        form.annotated_form,
        reg_spell_form.alt_phonology or reg_spell_form.annotated_form,
        SpellingType.GRAPHIC,
        Regularity.REGULAR_SPELLING_CHANGE,
    )


def _annotate_irreg_spell(form: MappedVerbForm, reg_spell_form: MappedVerbForm) -> None:
    irreg_spell = _annotate_irregularity(
        form.annotated_form,
        reg_spell_form.alt_phonology or reg_spell_form.annotated_form,
        SpellingType.GRAPHIC_NO_DIACRITICS,
        Regularity.IRREGULAR_SPELLING,
    )

    if irreg_spell is None:
        _annotate_reg_spell_change(form, reg_spell_form)


def _annotate_irreg_morph(form: MappedVerbForm, reg_morph_form: MappedVerbForm) -> None:
    irreg_morph = _annotate_irregularity(
        form.annotated_form,
        reg_morph_form.annotated_form,
        SpellingType.PHONETIC,
        Regularity.IRREGULAR_MORPHOLOGY,
    )

    if irreg_morph is None:
        return

    reg_suffix = reg_morph_form.annotated_form[irreg_morph.diff_stop :]
    reg_spell_change = next(
        (
            x
            for x in reg_suffix.get_annotations(Irregularity)
            if x.regularity is Regularity.REGULAR_SPELLING_CHANGE
        ),
        None,
    )

    if reg_spell_change is not None:
        form.annotated_form.add_annotation(
            replace(
                reg_spell_change,
                string=form.form,
                start=irreg_morph.stop + reg_spell_change.start,
                stop=irreg_morph.stop + reg_spell_change.stop,
            )
        )


def _annotate_irreg_constr(
    form: MappedVerbForm, reg_constr_form: MappedVerbForm
) -> None:
    _annotate_irregularity(
        form.annotated_form,
        reg_constr_form.annotated_form,
        SpellingType.GRAPHIC,
        Regularity.IRREGULAR_CONSTRUCTION,
    )


def _tag_irregularities(form: TaggedVerbForm) -> None:
    for x in form.value.annotated_form.get_annotations(Irregularity):
        form.tag(x.regularity)


def _annotate_irregularity(
    word: AnnotatedString,
    diff_word: AnnotatedString,
    spelling_type: SpellingType,
    tag: Regularity,
) -> Irregularity | None:
    diff_result = get_phonetic_diff(word, diff_word, spelling_type)
    if diff_result is None:
        return None

    irregularity = Irregularity(
        word.string,
        diff_result.start,
        diff_result.stop,
        diff_word.string[diff_result.diff_start : diff_result.diff_stop],
        tag,
    )

    word.add_annotation(irregularity)
    return irregularity
