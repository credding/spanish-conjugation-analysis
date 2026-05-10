from collections import defaultdict
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass, replace
from typing import TypeVar

from annotated_string import AnnotatedString, StringAnnotation
from ordered_enum import OrderedEnum
from spanish_conjugation import (
    RegularMorphologyConjugator,
    RegularSpellingConjugator,
    VerbConjugator,
)
from spanish_grammar import Inflection, Verb, VerbForm
from spanish_phonology import Phoneme, annotate_phonemes
from spanish_phonology.phonetics import TRANSLATE_REMOVE_DIACRITICS

from .grammar_index import GrammarIndex, TaggedVerb, TaggedVerbForm
from .grammar_index_model import IndexVerbForm, MappedVerbForm


class Regularity(OrderedEnum):
    MODEL_VERB = "verbo modelo"
    CORRECT_FORM = "forma correcta"
    CONSTRUCTED_FORM = "forma construida"
    REGULAR_MORPHOLOGY = "morfología regular"
    IRREGULAR_MORPHOLOGY = "morfología irregular"
    REGULAR_SPELLING = "ortografía regular"
    IRREGULAR_SPELLING = "ortografía irregular"
    REGULAR_SPELLING_CHANGE = "cambio ortográfico regular"
    REGULAR_CONSTRUCTION = "construcción regular"
    IRREGULAR_CONSTRUCTION = "construcción irregular"


@dataclass(repr=False)
class Irregularity(StringAnnotation):
    regularity: Regularity
    diff_text: str

    @property
    def diff_string(self) -> str:
        return f"{self.string[: self.start]}{self.diff_text}{self.string[self.stop :]}"

    @property
    def diff_stop(self) -> int:
        return self.stop - (len(self.text) - len(self.diff_text))

    def unique_key(self) -> Hashable:
        return type(self), self.regularity

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string[: self.start]}"
            f"[{self.diff_text or ''''''} -> {self.text or ''''''}]"
            f"{self.string[self.stop :]})"
            f"{super().__repr__()[:-1]}, "
            f"regularity={self.regularity!r})"
        )


class _RegularConstructionConjugator(RegularMorphologyConjugator):
    def __init__(self, index: GrammarIndex) -> None:
        self._index = index

    def _get_from_forms(
        self, verb_tag: Verb, from_conjug: Inflection | None
    ) -> list[AnnotatedString]:
        if from_conjug is None:
            return []

        correct_forms = self._index.lookup_verb_forms(
            Regularity.CORRECT_FORM, verb_tag, from_conjug
        )
        from_forms = []
        for form in sorted(correct_forms, key=lambda x: x.value.preference):
            from_form = AnnotatedString(form.value.form)
            annotate_phonemes(from_form)
            from_forms.append(from_form)

        return from_forms


class ConjugationAnalyzer:
    def __init__(self, index: GrammarIndex) -> None:
        self._index = index

        self._reg_spell_conjug = RegularSpellingConjugator()
        self._reg_morph_conjug = RegularMorphologyConjugator()
        self._reg_constr_conjug = _RegularConstructionConjugator(self._index)

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
        reg_annotated_forms = conjugator.conjugate(
            form_tag.lemma_tag, form_tag.inflection
        )

        for i, reg_annotated_form in enumerate(reg_annotated_forms):
            reg_form = self._index.index_verb_form(
                IndexVerbForm(
                    element_tag=replace(form_tag, form=reg_annotated_form.string),
                    preference=i,
                    alt_phonology=reg_annotated_form,
                )
            )
            reg_form.tag(regularity)

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
        eq=_eq_phoneme_text,
        tag=Regularity.REGULAR_SPELLING_CHANGE,
    )


def _annotate_irreg_spell(form: MappedVerbForm, reg_spell_form: MappedVerbForm) -> None:
    irreg_spell = _annotate_irregularity(
        form.annotated_form,
        reg_spell_form.alt_phonology or reg_spell_form.annotated_form,
        eq=_eq_phoneme_text_norm,
        tag=Regularity.IRREGULAR_SPELLING,
    )

    if irreg_spell is None:
        _annotate_reg_spell_change(form, reg_spell_form)


def _annotate_irreg_morph(form: MappedVerbForm, reg_morph_form: MappedVerbForm) -> None:
    irreg_morph = _annotate_irregularity(
        form.annotated_form,
        reg_morph_form.annotated_form,
        eq=_eq_phoneme,
        tag=Regularity.IRREGULAR_MORPHOLOGY,
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
        eq=_eq_phoneme_text,
        tag=Regularity.IRREGULAR_CONSTRUCTION,
    )


def _tag_irregularities(form: TaggedVerbForm) -> None:
    for x in form.value.annotated_form.get_annotations(Irregularity):
        form.tag(x.regularity)


def _annotate_irregularity(
    word: AnnotatedString,
    diff_word: AnnotatedString,
    /,
    *,
    eq: Callable[[Phoneme, Phoneme], bool],
    tag: Regularity,
) -> Irregularity | None:
    phonemes = word.get_annotations(Phoneme)
    diff_phonemes = diff_word.get_annotations(Phoneme)

    diff_range = _get_diff_range(phonemes, diff_phonemes, eq=eq)
    if diff_range is None:
        return None

    start_phoneme, stop_phoneme = diff_range

    start = _get_phoneme_text_index(phonemes, start_phoneme)
    diff_start = _get_phoneme_text_index(diff_phonemes, start_phoneme)

    len_diff = len(phonemes) - len(diff_phonemes)

    stop = _get_phoneme_text_index(phonemes, stop_phoneme)
    diff_stop = _get_phoneme_text_index(diff_phonemes, stop_phoneme - len_diff)

    return word.annotate(
        Irregularity, start, stop, tag, diff_word.string[diff_start:diff_stop]
    )


def _get_phoneme_text_index(phonemes: Sequence[Phoneme], index: int) -> int:
    return phonemes[index].start if index < len(phonemes) else len(phonemes[-1].string)


_T = TypeVar("_T")


def _get_diff_range(
    string: Sequence[_T],
    diff_string: Sequence[_T],
    /,
    *,
    eq: Callable[[_T, _T], bool] = lambda x, y: x == y,
) -> tuple[int, int] | None:
    start = 0
    while (
        start < len(string)
        and start < len(diff_string)
        and eq(string[start], diff_string[start])
    ):
        start += 1

    if len(string) == len(diff_string) == start:
        return None

    len_diff = len(string) - len(diff_string)

    stop = len(string)
    while (
        stop > start
        and stop > len_diff
        and eq(string[stop - 1], diff_string[stop - len_diff - 1])
    ):
        stop -= 1

    return start, stop


def _eq_phoneme(a: Phoneme, b: Phoneme) -> bool:
    return (a.phoneme_kind, a.phoneme) == (b.phoneme_kind, b.phoneme)


def _eq_phoneme_text(a: Phoneme, b: Phoneme) -> bool:
    return a.text == b.text


def _eq_phoneme_text_norm(a: Phoneme, b: Phoneme) -> bool:
    a_text_norm = a.text.translate(TRANSLATE_REMOVE_DIACRITICS)
    b_text_norm = b.text.translate(TRANSLATE_REMOVE_DIACRITICS)
    return a_text_norm == b_text_norm
