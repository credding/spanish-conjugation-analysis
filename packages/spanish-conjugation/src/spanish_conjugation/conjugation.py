import logging
from abc import ABC, abstractmethod
from dataclasses import replace

from annotated_string import AnnotatedString
from spanish_grammar import Inflection, Verb
from spanish_phonology import Phoneme, annotate_next_phoneme, annotate_phonemes
from spanish_phonology.phonetics import (
    HARD_VOWELS,
    SOFT_VOWELS,
    STRONG_VOWELS,
    TRANSLATE_ADD_STRESS,
    VOWELS,
)

from .conjugation_spec import ConjugationSpec, get_conjugation_spec

_logger = logging.getLogger(__name__)


class VerbConjugator(ABC):
    @abstractmethod
    def conjugate(self, verb: Verb, inflection: Inflection) -> list[AnnotatedString]:
        raise NotImplementedError


class RegularSpellingConjugator(VerbConjugator):
    def conjugate(self, verb: Verb, inflection: Inflection) -> list[AnnotatedString]:
        spec = get_conjugation_spec(verb, inflection)
        if spec is None:
            return []

        result: list[AnnotatedString] = []

        for from_form in self._get_from_forms(verb, spec.from_conjug):
            form = self._conjugate_form(spec, from_form)
            if form is not None:
                result.append(form)

        return result

    def _conjugate_form(
        self, spec: ConjugationSpec, stem: AnnotatedString
    ) -> AnnotatedString | None:
        if not stem.string.endswith(spec.truncate_str):
            return None

        if len(spec.truncate_str) > 0:
            stem = stem[: -len(spec.truncate_str)]

        if spec.affix == "":
            return stem

        affix = self._adapt_affix(stem, spec.affix)
        stem = self._adapt_stem(stem, affix)

        if spec.pre_affix_stress:
            last_phoneme = stem.get_annotations(Phoneme)[-1]
            stem = _replace_phoneme(
                stem, last_phoneme, last_phoneme.text.translate(TRANSLATE_ADD_STRESS)
            )

        affix = AnnotatedString(affix)
        annotate_phonemes(affix)

        return stem + affix

    def _adapt_affix(self, stem: AnnotatedString, affix: str) -> str:  # noqa: ARG002
        return affix

    def _adapt_stem(self, stem: AnnotatedString, affix: str) -> AnnotatedString:  # noqa: ARG002
        return stem

    def _get_from_forms(
        self, verb_tag: Verb, from_conjug: Inflection | None
    ) -> list[AnnotatedString]:
        if from_conjug is None:
            infinitive_form = AnnotatedString(verb_tag.infinitive)
            annotate_phonemes(infinitive_form)
            return [infinitive_form]
        return self.conjugate(verb_tag, from_conjug)


class RegularMorphologyConjugator(RegularSpellingConjugator):
    def _adapt_affix(self, stem: AnnotatedString, affix: str) -> str:
        if stem.string == "" or len(affix) < 2:  # noqa: PLR2004
            return affix

        stem_phonemes = stem.get_annotations(Phoneme)

        if affix[0] == "i":
            if affix[1] in VOWELS:
                if stem_phonemes[-1].phoneme in VOWELS:
                    # /<vowel>i<vowel>/ sounds like /<vowel>y<vowel>/
                    # /<vowel>i<vowel>/ occurs in a few non-verbs in the Spanish
                    # language
                    return "y" + affix[1:]
                if stem_phonemes[-1].phoneme in "ñy":
                    # /<ñy>i<vowel>/ sounds like /<ñy><vowel>/
                    # /<ñy>i<vowel>/ does not occur in the Spanish language
                    return affix[1:]
            elif stem_phonemes[-1].phoneme in STRONG_VOWELS:
                # maintains stress, not sound
                # only occurs for -ido, -imos, -iste
                return "í" + affix[1:]

        return affix

    def _adapt_stem(self, stem: AnnotatedString, affix: str) -> AnnotatedString:
        if stem.string == "" or affix == "":
            return stem

        phonemes = stem.get_annotations(Phoneme)
        last_phoneme_text = None

        if affix[0] in SOFT_VOWELS:
            last_phoneme_text = _get_last_phoneme_text_for_soft_vowel(phonemes)
        elif affix[0] in HARD_VOWELS:
            last_phoneme_text = _get_last_phoneme_text_for_hard_vowel(phonemes)

        if last_phoneme_text is None:
            return stem

        return _replace_phoneme_text(stem, phonemes[-1], last_phoneme_text)


def _get_last_phoneme_text_for_soft_vowel(phonemes: list[Phoneme]) -> str | None:
    key = phonemes[-1].phoneme, phonemes[-1].text

    if (
        key == ("u", "u")
        and len(phonemes) >= 2  # noqa: PLR2004
        and phonemes[-2].phoneme == "g"
    ):
        return "ü"

    return {("g", "g"): "gu", ("k", "c"): "qu", ("s", "z"): "c"}.get(key)


def _get_last_phoneme_text_for_hard_vowel(phonemes: list[Phoneme]) -> str | None:
    key = phonemes[-1].phoneme, phonemes[-1].text

    return {
        ("u", "ü"): "u",
        ("g", "gu"): "g",
        ("k", "qu"): "c",
        ("s", "c"): "z",
        ("x", "g"): "j",
    }.get(key)


def _replace_phoneme(
    string: AnnotatedString, phoneme: Phoneme, new_text: str
) -> AnnotatedString:
    string = string[: phoneme.start] + new_text + string[phoneme.stop :]
    annotate_next_phoneme(string, phoneme.start)
    return string


def _replace_phoneme_text(
    string: AnnotatedString, phoneme: Phoneme, new_text: str
) -> AnnotatedString:
    string = string[: phoneme.start] + new_text + string[phoneme.stop :]
    string.add_annotation(
        replace(
            phoneme,
            string=string.string,
            start=phoneme.start,
            stop=phoneme.start + len(new_text),
        )
    )
    return string
