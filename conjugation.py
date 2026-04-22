import csv
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from diff_analysis import DiffAnnotation, annotate_diff
from grammar_model import Regularity, Subject, Tense, Variant, Verb, VerbForm
from resources import resources_path
from phonetic_analysis import (
    SOFT_VOWELS,
    TRANSLATE_ADD_STRESS,
    VOWELS,
    Phoneme,
    annotate_phonemes, PhonemeKind,
)
from string_analysis import AnnotatedString, StringAnnotation
from element_index import ElementIndex


@dataclass(eq=False, repr=False)
class VerbAffix(StringAnnotation):
    pass


@dataclass(eq=False, repr=False)
class VerbSubject(StringAnnotation):
    pass


@dataclass(eq=False, repr=False)
class VerbVariant(StringAnnotation):
    pass


@dataclass(eq=False, repr=False)
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


class SimpleConjugator(VerbConjugator):
    def conjugate(
        self,
        verb: Verb,
        tense: Tense,
        subject: Subject,
        variant: Variant | None,
    ) -> list[AnnotatedString]:
        key = _VerbFormSpecKey(verb.ending, tense, subject, variant)
        spec = _REGULAR_CONJUGATION_LOOKUP.get(key)
        if not spec:
            return []

        form_candidates = []

        for from_form in self._get_from_form_candidates(
            verb, spec.from_tense, spec.from_subject
        ):
            stem = from_form[:]
            annotate_phonemes(stem)

            if spec.truncate_str:
                if not re.search(spec.truncate_str.replace("_", ".") + "$", stem.text):
                    continue
                stem = stem[: -len(spec.truncate_str)]

            form = self._conjugate_form(subject, variant, stem, spec)
            form.remove_annotations(Phoneme)

            form_candidates.append(form)

        return form_candidates

    def _conjugate_form(
        self,
        subject: Subject,
        variant: Variant | None,
        stem: AnnotatedString,
        spec: _VerbFormSpec,
    ) -> AnnotatedString:
        if not spec.affix:
            return stem

        affix = self._adapt_affix(stem, spec.affix)
        stem = self._adapt_stem(stem, affix)

        if spec.pre_affix_stress:
            stem.text = stem.text[:-1] + stem.text[-1].translate(TRANSLATE_ADD_STRESS)

        form = AnnotatedString(stem.text + affix)

        affix_annotation = stem.remove_annotation(VerbAffix)
        if affix_annotation:
            affix_start = affix_annotation.start
        else:
            affix_start = len(stem.text)

        form.annotate(VerbAffix, affix_start, len(form.text))

        if subject is not Subject.IMPERSONAL:
            subject_annotation = stem.remove_annotation(VerbSubject)
            if subject_annotation:
                subject_start = subject_annotation.start
            else:
                subject_start = len(stem.text)
            if spec.subject_len:
                subject_start = len(form.text) - spec.subject_len

            form.annotate(VerbSubject, subject_start, len(form.text))

        if variant:
            form.annotate(VerbVariant, len(stem.text), len(stem.text) + 2)

        return form

    def _get_from_form_candidates(
        self, verb: Verb, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if not tense or not subject:
            return [AnnotatedString(verb.infinitive)]
        return self.conjugate(verb, tense, subject, None)

    def _adapt_affix(self, stem: AnnotatedString, affix: str) -> str:
        return affix

    def _adapt_stem(self, stem: AnnotatedString, affix: str) -> AnnotatedString:
        return stem


class RegularFormConjugator(SimpleConjugator):
    _simple_conjugator: SimpleConjugator = SimpleConjugator()

    def _conjugate_form(
        self,
        subject: Subject,
        variant: Variant | None,
        stem: AnnotatedString,
        spec: _VerbFormSpec,
    ) -> AnnotatedString:
        regular_form = super()._conjugate_form(subject, variant, stem, spec)

        simple_form = self._simple_conjugator._conjugate_form(
            subject, variant, stem, spec
        )

        annotate_diff(SpellingChange, regular_form, simple_form.text)

        return regular_form

    def _adapt_affix(self, stem: AnnotatedString, affix: str) -> str:
        if not stem.text or len(affix) < 2:
            return affix

        stem_phonemes = stem.get_annotations(Phoneme)

        if affix[0] == "i":
            if affix[1] in VOWELS:
                if stem_phonemes[-1].phoneme_kind in (PhonemeKind.STRONG_VOWEL, PhonemeKind.WEAK_VOWEL):
                    return "y" + affix[1:]
                elif stem_phonemes[-1].phoneme in ("y", "ñ"):
                    return affix[1:]
            elif stem_phonemes[-1].phoneme_kind is PhonemeKind.STRONG_VOWEL:
                return "í" + affix[1:]

        return affix

    def _adapt_stem(self, stem: AnnotatedString, affix: str) -> AnnotatedString:
        if not stem.text or not affix:
            return stem

        stem_phonemes = stem.get_annotations(Phoneme)

        match stem_phonemes[-1].phoneme, stem_phonemes[-1].text, affix[0] in SOFT_VOWELS:
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


class RegularConstructionConjugator(RegularFormConjugator):
    def __init__(self, index: ElementIndex):
        self._index = index

    def _get_from_form_candidates(
        self, verb: Verb, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if not tense or not subject:
            return []
        return [
            x.annotated_form
            for x in sorted(
                self._index.lookup(VerbForm, Regularity.CORRECT_FORM, verb, tense, subject),
                key=lambda x: x.element.preference,
            )
        ]


@dataclass(frozen=True)
class _VerbFormSpecKey:
    ending: str
    tense: Tense
    subject: Subject | None
    variant: Variant | None


@dataclass(frozen=True)
class _VerbFormSpec:
    from_tense: Tense | None
    from_subject: Subject | None
    truncate_str: str
    pre_affix_stress: bool
    affix: str
    subject_len: int | None


def _load_regular_conjugation_lookup() -> dict[_VerbFormSpecKey, _VerbFormSpec]:
    result: dict[_VerbFormSpecKey, _VerbFormSpec] = {}
    conjugation_data_path = resources_path.joinpath("regular_conjugation.csv")
    with conjugation_data_path.open("r", newline="") as f:
        reader = csv.DictReader(f, dialect=csv.unix_dialect)
        for row in reader:
            for ending in row["endings"].split(";"):
                for subject in row["subjects"].split(";"):
                    key = _VerbFormSpecKey(
                        ending=ending,
                        tense=Tense(row["tense"]),
                        subject=Subject(subject) if subject else None,
                        variant=Variant(row["variant"]) if row["variant"] else None,
                    )
                    result[key] = _VerbFormSpec(
                        from_tense=Tense(row["from_tense"])
                        if row["from_tense"]
                        else None,
                        from_subject=Subject(row["from_subject"])
                        if row["from_subject"]
                        else None,
                        truncate_str=row["truncate_str"],
                        pre_affix_stress=row["pre_affix_stress"] == "1",
                        affix=row["affix"],
                        subject_len=int(row["subject_len"])
                        if row["subject_len"]
                        else None,
                    )
    return result


_REGULAR_CONJUGATION_LOOKUP = _load_regular_conjugation_lookup()
