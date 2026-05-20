import pytest
from annotated_string import AnnotatedString
from spanish_conjugation import RegularMorphologyConjugator, RegularSpellingConjugator
from spanish_grammar import Inflection, Subject, Tense, Variant, Verb
from spanish_phonology import SpellingType, get_phonetic_form

from .test_data import (
    CORRECT_REGULAR_MORPHOLOGY_FORMS,
    CORRECT_REGULAR_SPELLING_FORMS,
    INCORRECT_REGULAR_SPELLING_FORMS,
)


class TestRegularSpellingConjugation:
    @pytest.mark.parametrize(
        ("_form", "verb", "tense", "subject", "variant", "expected_annotated_form"),
        CORRECT_REGULAR_SPELLING_FORMS + INCORRECT_REGULAR_SPELLING_FORMS,
    )
    def test_known_regular_spelling_forms(
        self,
        _form: str,
        verb: str,
        tense: Tense,
        subject: Subject,
        variant: Variant,
        expected_annotated_form: AnnotatedString,
    ) -> None:
        conjugator = RegularSpellingConjugator()
        result = conjugator.conjugate(Verb(verb), Inflection(tense, subject, variant))

        assert len(result) == 1
        assert result[0] == expected_annotated_form

    @pytest.mark.parametrize(
        ("verb", "tense", "subject", "expected_form", "expected_phonetic_form"),
        [
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_gues", "_gues"),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_gue", "_gue"),
            (
                "_guar",
                Tense.SUBJUNCTIVE_PRESENT,
                Subject.NOSOTROS,
                "_guemos",
                "_guemos",
            ),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_guéis", "_guéis"),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_guen", "_guen"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_ges", "_ges"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ge", "_ge"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_gemos", "_gemos"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_géis", "_géis"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_gen", "_gen"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_ces", "_kes"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ce", "_ke"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_cemos", "_kemos"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_céis", "_kéis"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_cen", "_ken"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_zes", "_ses"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ze", "_se"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_zemos", "_semos"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_zéis", "_séis"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_zen", "_sen"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_güas", "_guas"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_güa", "_gua"),
            (
                "_güer",
                Tense.SUBJUNCTIVE_PRESENT,
                Subject.NOSOTROS,
                "_güamos",
                "_guamos",
            ),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_güáis", "_guáis"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_güan", "_guan"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_guas", "_gas"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_gua", "_ga"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_guamos", "_gamos"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_guáis", "_gáis"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_guan", "_gan"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_quas", "_kas"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_qua", "_ka"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_quamos", "_kamos"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_quáis", "_káis"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_quan", "_kan"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_cas", "_sas"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ca", "_sa"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_camos", "_samos"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_cáis", "_sáis"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_can", "_san"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_gas", "_xas"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ga", "_xa"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_gamos", "_xamos"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_gáis", "_xáis"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_gan", "_xan"),
        ],
    )
    def test_regular_spelling_phonology(
        self,
        verb: str,
        tense: Tense,
        subject: Subject,
        expected_form: str,
        expected_phonetic_form: str,
    ) -> None:
        conjugator = RegularSpellingConjugator()
        result = conjugator.conjugate(Verb(verb), Inflection(tense, subject, None))

        assert len(result) == 1
        assert result[0].string == expected_form
        assert (
            get_phonetic_form(result[0], SpellingType.PHONETIC).form
            == expected_phonetic_form
        )


class TestRegularMorphologyConjugation:
    @pytest.mark.parametrize(
        ("_form", "verb", "tense", "subject", "variant", "expected_annotated_form"),
        CORRECT_REGULAR_SPELLING_FORMS + CORRECT_REGULAR_MORPHOLOGY_FORMS,
    )
    def test_known_regular_morphology_forms(
        self,
        _form: str,
        verb: str,
        tense: Tense,
        subject: Subject,
        variant: Variant | None,
        expected_annotated_form: AnnotatedString,
    ) -> None:
        conjugator = RegularMorphologyConjugator()
        result = conjugator.conjugate(Verb(verb), Inflection(tense, subject, variant))

        assert len(result) == 1
        assert result[0] == expected_annotated_form

    @pytest.mark.parametrize(
        ("verb", "tense", "subject", "expected_form", "expected_phonetic_form"),
        [
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_gües", "_gues"),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_güe", "_gue"),
            (
                "_guar",
                Tense.SUBJUNCTIVE_PRESENT,
                Subject.NOSOTROS,
                "_güemos",
                "_guemos",
            ),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_güéis", "_guéis"),
            ("_guar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_güen", "_guen"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_gues", "_ges"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_gue", "_ge"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_guemos", "_gemos"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_guéis", "_géis"),
            ("_gar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_guen", "_gen"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_ques", "_kes"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_que", "_ke"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_quemos", "_kemos"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_quéis", "_kéis"),
            ("_car", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_quen", "_ken"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_ces", "_ses"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ce", "_se"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_cemos", "_semos"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_céis", "_séis"),
            ("_zar", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_cen", "_sen"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_guas", "_guas"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_gua", "_gua"),
            (
                "_güer",
                Tense.SUBJUNCTIVE_PRESENT,
                Subject.NOSOTROS,
                "_guamos",
                "_guamos",
            ),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_guáis", "_guáis"),
            ("_güer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_guan", "_guan"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_gas", "_gas"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ga", "_ga"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_gamos", "_gamos"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_gáis", "_gáis"),
            ("_guer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_gan", "_gan"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_cas", "_kas"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ca", "_ka"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_camos", "_kamos"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_cáis", "_káis"),
            ("_quer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_can", "_kan"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_zas", "_sas"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_za", "_sa"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_zamos", "_samos"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_záis", "_sáis"),
            ("_cer", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_zan", "_san"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.TU, "_jas", "_xas"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA, "_ja", "_xa"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.NOSOTROS, "_jamos", "_xamos"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.VOSOTROS, "_jáis", "_xáis"),
            ("_ger", Tense.SUBJUNCTIVE_PRESENT, Subject.USTEDES, "_jan", "_xan"),
        ],
    )
    def test_regular_morpholgy_phonology(
        self,
        verb: str,
        tense: Tense,
        subject: Subject,
        expected_form: str,
        expected_phonetic_form: str,
    ) -> None:
        conjugator = RegularMorphologyConjugator()
        result = conjugator.conjugate(Verb(verb), Inflection(tense, subject, None))

        assert len(result) == 1
        assert result[0].string == expected_form
        assert (
            get_phonetic_form(result[0], SpellingType.PHONETIC).form
            == expected_phonetic_form
        )
