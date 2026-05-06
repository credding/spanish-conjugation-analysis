import logging
from abc import ABC, abstractmethod
from dataclasses import replace

from annotated_string import AnnotatedString
from conjugation_spec import ConjugationSpec, get_conjugation_spec
from grammar_model import (
    Element,
    ElementTag,
    Regularity,
    Subject,
    Tense,
    Variant,
    VerbTag,
)
from phonetic_analysis import (
    HARD_VOWELS,
    SOFT_VOWELS,
    STRONG_VOWELS,
    TRANSLATE_ADD_STRESS,
    VOWELS,
    Phoneme,
    annotate_phonemes,
)
from tagged_index import TaggedIndex

_logger = logging.getLogger(__name__)


class VerbConjugator(ABC):
    @abstractmethod
    def conjugate(
        self, verb_tag: VerbTag, tense: Tense, subject: Subject, variant: Variant | None
    ) -> list[AnnotatedString]:
        raise NotImplementedError


class RegularSpellingConjugator(VerbConjugator):
    def conjugate(
        self, verb_tag: VerbTag, tense: Tense, subject: Subject, variant: Variant | None
    ) -> list[AnnotatedString]:
        spec = get_conjugation_spec(verb_tag, tense, subject, variant)
        if spec is None:
            return []

        result: list[AnnotatedString] = []

        for from_form in self._get_from_forms(
            verb_tag, spec.from_tense, spec.from_subject
        ):
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
            stem_phonemes = stem.get_annotations(Phoneme)
            last_phoneme = stem_phonemes[-1]
            stem = _replace_phoneme_text(
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
        self, verb_tag: VerbTag, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if tense is None or subject is None:
            return [_annotate_phonemes(verb_tag.infinitive)]
        return self.conjugate(verb_tag, tense, subject, None)


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

        if affix[0] in SOFT_VOWELS:
            return _adapt_stem_to_soft_vowel(stem)
        if affix[0] in HARD_VOWELS:
            return _adapt_stem_to_hard_vowel(stem)
        return stem


def _adapt_stem_to_soft_vowel(stem: AnnotatedString) -> AnnotatedString:
    stem_phonemes = stem.get_annotations(Phoneme)
    last_phoneme = stem_phonemes[-1]

    match (last_phoneme.phoneme, last_phoneme.text):
        case "u", "u":
            if len(stem_phonemes) >= 2 and stem_phonemes[-2].phoneme == "g":  # noqa: PLR2004
                stem = _replace_phoneme_text(stem, last_phoneme, "ü")
        case "g", "g":
            stem = _replace_phoneme_text(stem, last_phoneme, "gu")
        case "k", "c":
            stem = _replace_phoneme_text(stem, last_phoneme, "qu")
        case "s", "z":
            stem = _replace_phoneme_text(stem, last_phoneme, "c")

    return stem


def _adapt_stem_to_hard_vowel(stem: AnnotatedString) -> AnnotatedString:
    stem_phonemes = stem.get_annotations(Phoneme)
    last_phoneme = stem_phonemes[-1]

    match (last_phoneme.phoneme, last_phoneme.text):
        case "u", "ü":
            stem = _replace_phoneme_text(stem, last_phoneme, "u")
        case "g", "gu":
            stem = _replace_phoneme_text(stem, last_phoneme, "g")
        case "k", "qu":
            stem = _replace_phoneme_text(stem, last_phoneme, "c")
        case "s", "c":
            stem = _replace_phoneme_text(stem, last_phoneme, "z")
        case "x", "g":
            stem = _replace_phoneme_text(stem, last_phoneme, "j")

    return stem


class RegularConstructionConjugator(RegularMorphologyConjugator):
    def __init__(self, index: TaggedIndex[ElementTag, Element]) -> None:
        self._index = index

    def _get_from_forms(
        self, verb_tag: VerbTag, tense: Tense | None, subject: Subject | None
    ) -> list[AnnotatedString]:
        if tense is None or subject is None:
            return []
        return [
            _annotate_phonemes(x.value.form)
            for x in sorted(
                self._index.lookup(Regularity.CORRECT_FORM, verb_tag, tense, subject),
                key=lambda x: x.value.preference,
            )
        ]


def _annotate_phonemes(word: str) -> AnnotatedString:
    string = AnnotatedString(word)
    annotate_phonemes(string)
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
