import csv
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache

from diff_analysis import DiffAnnotation, annotate_diff
from element_index import ElementIndex
from grammar_model import Regularity, Subject, Tense, Variant, Verb, VerbForm
from phonetic_analysis import (
    SOFT_VOWELS,
    TRANSLATE_ADD_STRESS,
    VOWELS,
    Phoneme,
    PhonemeKind,
    annotate_phonemes,
)
from resources import resources_path
from string_analysis import AnnotatedString, StringAnnotation


@dataclass(frozen=True, eq=False, repr=False)
class VerbAffix(StringAnnotation):
    pass


@dataclass(frozen=True, eq=False, repr=False)
class VerbSubject(StringAnnotation):
    pass


@dataclass(frozen=True, eq=False, repr=False)
class VerbVariant(StringAnnotation):
    pass


@dataclass(frozen=True, eq=False, repr=False)
class SpellingChange(DiffAnnotation):
    pass


class VerbConjugator(ABC):
    @abstractmethod
    def conjugate(
        self,
        verb: Verb,
        tense: Tense,
        subject: Subject,
        variant: Variant | None,
    ) -> list[AnnotatedString]:
        pass


class RegularFormConjugator(VerbConjugator):
    def conjugate(
        self,
        verb: Verb,
        tense: Tense,
        subject: Subject,
        variant: Variant | None,
    ) -> list[AnnotatedString]:
        spec_key = _VerbFormSpecKey(verb.ending, tense, subject, variant)
        spec = _REGULAR_CONJUGATION_LOOKUP.get(spec_key)
        if spec is None:
            return []

        form_candidates: list[AnnotatedString] = []

        for from_form in self._get_from_form_candidates(
            verb, spec.from_tense, spec.from_subject
        ):
            form = _conjugate_form(from_form, spec)
            if form is not None:
                form_candidates.append(form)

        return form_candidates

    def _get_from_form_candidates(
        self, verb: Verb, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if tense is None or subject is None:
            return [_infinitive_form(verb)]
        return self.conjugate(verb, tense, subject, None)


class RegularConstructionConjugator(RegularFormConjugator):
    def __init__(self, index: ElementIndex):
        self._index = index

    def _get_from_form_candidates(
        self, verb: Verb, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if tense is None or subject is None:
            return []
        return [
            x.annotated_form
            for x in sorted(
                self._index.lookup(
                    VerbForm, Regularity.CORRECT_FORM, verb, tense, subject
                ),
                key=lambda x: x.element.preference,
            )
        ]


@cache
def _infinitive_form(verb: Verb) -> AnnotatedString:
    return AnnotatedString(verb.infinitive)


@cache
def _conjugate_form(
    from_form: AnnotatedString, spec: _VerbFormSpec
) -> AnnotatedString | None:
    stem = from_form[:]
    annotate_phonemes(stem)

    if spec.truncate_len > 0:
        assert spec.truncate_pattern
        if not spec.truncate_pattern.search(stem.text):
            return None
        stem = stem[: -spec.truncate_len]

    if spec.affix == "":
        return stem

    if spec.pre_affix_stress:
        stem.text = stem.text[:-1] + stem.text[-1].translate(TRANSLATE_ADD_STRESS)

    simple_form = stem.text + spec.affix

    affix = _adapt_affix(stem, spec.affix)
    stem = _adapt_stem(stem, affix)

    form = stem + affix

    affix_annotation = form.remove_annotation(VerbAffix, raise_if_absent=False)
    if affix_annotation is not None:
        affix_start = affix_annotation.start
    else:
        affix_start = len(stem.text)

    form.annotate(VerbAffix, affix_start, len(form.text))

    if len(spec.subjects) > 0:
        subject_annotation = form.remove_annotation(VerbSubject, raise_if_absent=False)
        if subject_annotation is not None:
            subject_start = subject_annotation.start
        else:
            subject_start = len(stem.text)
        if spec.subject_len is not None:
            assert spec.subject_len > 0
            subject_start = len(form.text) - spec.subject_len

        form.annotate(VerbSubject, subject_start, len(form.text))

    if spec.variant is not None:
        form.annotate(VerbVariant, len(stem.text), len(stem.text) + 2)

    annotate_diff(SpellingChange, form, simple_form)

    form.remove_annotations(Phoneme)
    return form


def _adapt_affix(stem: AnnotatedString, affix: str) -> str:
    if stem.text == "" or len(affix) < 2:
        return affix

    stem_phonemes = stem.get_annotations(Phoneme)

    if affix[0] == "i":
        if affix[1] in VOWELS:
            if stem_phonemes[-1].phoneme_kind in (
                PhonemeKind.STRONG_VOWEL,
                PhonemeKind.WEAK_VOWEL,
            ):
                return "y" + affix[1:]
            elif stem_phonemes[-1].phoneme in ("y", "ñ"):
                return affix[1:]
        elif stem_phonemes[-1].phoneme_kind is PhonemeKind.STRONG_VOWEL:
            return "í" + affix[1:]

    return affix


def _adapt_stem(stem: AnnotatedString, affix: str) -> AnnotatedString:
    if stem.text == "" or affix == "":
        return stem

    stem_phonemes = stem.get_annotations(Phoneme)

    match (
        stem_phonemes[-1].phoneme,
        stem_phonemes[-1].text,
        affix[0] in SOFT_VOWELS,
    ):
        case "u", "u", True:
            if len(stem_phonemes) >= 2 and stem_phonemes[-2].phoneme == "g":
                return stem[:-1] + "ü"
        case "u", "ü", False:
            return stem[:-1] + "u"
        case "g", "g", True:
            return stem[:-1] + "gu"
        case "g", "gu", False:
            return stem[:-2] + "g"
        case "k", "c", True:
            return stem[:-1] + "qu"
        case "k", "qu", False:
            return stem[:-2] + "c"
        case "s", "z", True:
            return stem[:-1] + "c"
        case "s", "c", False:
            return stem[:-1] + "z"
        case "j", "g", False:
            return stem[:-1] + "j"

    return stem


@dataclass(frozen=True)
class _VerbFormSpecKey:
    ending: str
    tense: Tense
    subject: Subject
    variant: Variant | None


@dataclass(frozen=True)
class _VerbFormSpec:
    subjects: tuple[Subject, ...]
    variant: Variant | None
    from_tense: Tense | None
    from_subject: Subject | None
    truncate_len: int
    truncate_pattern: re.Pattern | None
    pre_affix_stress: bool
    affix: str
    subject_len: int | None


def _load_regular_conjugation_lookup() -> dict[_VerbFormSpecKey, _VerbFormSpec]:
    result: dict[_VerbFormSpecKey, _VerbFormSpec] = {}
    conjugation_data_path = resources_path / "regular_conjugation.csv"
    with conjugation_data_path.open("r", newline="") as f:
        reader = csv.DictReader(f, dialect=csv.unix_dialect)
        for row in reader:
            tense = Tense(row["tense"])
            subjects = (
                [Subject(x) for x in row["subjects"].split(";")]
                if row["subjects"]
                else []
            )
            variant = Variant(row["variant"]) if row["variant"] else None
            spec = _VerbFormSpec(
                subjects=tuple(subjects),
                variant=variant,
                from_tense=Tense(row["from_tense"]) if row["from_tense"] else None,
                from_subject=Subject(row["from_subject"])
                if row["from_subject"]
                else None,
                truncate_len=len(row["truncate_str"]),
                truncate_pattern=re.compile(row["truncate_str"].replace("_", ".") + "$")
                if row["truncate_str"]
                else None,
                pre_affix_stress=row["pre_affix_stress"] == "1",
                affix=row["affix"],
                subject_len=int(row["subject_len"]) if row["subject_len"] else None,
            )
            for ending in row["endings"].split(";"):
                for subject in subjects or [Subject.IMPERSONAL]:
                    key = _VerbFormSpecKey(
                        ending=ending,
                        tense=tense,
                        subject=subject,
                        variant=variant,
                    )
                    result[key] = spec
    return result


_REGULAR_CONJUGATION_LOOKUP = _load_regular_conjugation_lookup()
