import pytest
from annotated_string import AnnotatedString
from spanish_conjugation import RegularMorphologyConjugator, RegularSpellingConjugator
from spanish_grammar import Inflection, Verb

from .test_data import (
    CORRECT_REGULAR_MORPHOLOGY_FORMS,
    CORRECT_REGULAR_SPELLING_FORMS,
    INCORRECT_REGULAR_SPELLING_FORMS,
)


class TestRegularSpellingConjugation:
    @pytest.mark.parametrize(
        ("_form", "verb", "inflection", "expected_annotated_form"),
        CORRECT_REGULAR_SPELLING_FORMS + INCORRECT_REGULAR_SPELLING_FORMS,
    )
    def test_known_regular_spelling_forms(
        self,
        _form: str,
        verb: Verb,
        inflection: Inflection,
        expected_annotated_form: AnnotatedString,
    ) -> None:
        conjugator = RegularSpellingConjugator()
        result = conjugator.conjugate(verb, inflection)
        assert len(result) == 1
        assert result[0] == expected_annotated_form


class TestRegularMorphologyConjugation:
    @pytest.mark.parametrize(
        ("_form", "verb", "inflection", "expected_annotated_form"),
        CORRECT_REGULAR_SPELLING_FORMS + CORRECT_REGULAR_MORPHOLOGY_FORMS,
    )
    def test_known_regular_morphology_forms(
        self,
        _form: str,
        verb: Verb,
        inflection: Inflection,
        expected_annotated_form: AnnotatedString,
    ) -> None:
        conjugator = RegularMorphologyConjugator()
        result = conjugator.conjugate(verb, inflection)
        assert len(result) == 1
        assert result[0] == expected_annotated_form
