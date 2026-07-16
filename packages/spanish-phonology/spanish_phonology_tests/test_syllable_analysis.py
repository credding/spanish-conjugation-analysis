# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from annotated_string import AnnotatedString
from spanish_phonology import Syllable, annotate_phonemes, annotate_syllables


def with_phonemes(word: str) -> AnnotatedString:
    string = AnnotatedString(word)
    annotate_phonemes(string)
    return string


class TestAnnotateSyllables:
    def test_empty(self) -> None:
        word = with_phonemes("")
        syllables = annotate_syllables(word)

        assert word.get_annotations(Syllable) == syllables
        assert syllables == []

    # Reference: https://catalog.ldc.upenn.edu/docs/LDC2019S07/Syllabification_Rules_in_Spanish.pdf
    # Supporting reference: https://baselang.com/blog/pronunciation/spanish-syllables/
    @pytest.mark.parametrize(
        ("text", "expected_syllables"),
        [
            # open syllables
            ("caballo", ["ca", "ba", "llo"]),
            ("maleta", ["ma", "le", "ta"]),
            ("sótano", ["só", "ta", "no"]),
            ("abuelo", ["a", "bue", "lo"]),
            # closed syllables
            ("charlar", ["char", "lar"]),
            ("mártir", ["már", "tir"]),
            ("costar", ["cos", "tar"]),
            ("mandar", ["man", "dar"]),
            # consonant between two vowels
            ("casa", ["ca", "sa"]),
            ("miraron", ["mi", "ra", "ron"]),
            ("demora", ["de", "mo", "ra"]),
            # bilabial consonant with liquid consonant
            ("oprimo", ["o", "pri", "mo"]),
            ("obrero", ["o", "bre", "ro"]),
            ("aplomo", ["a", "plo", "mo"]),
            ("hablando", ["ha", "blan", "do"]),
            # labiodental consonant with liquid consonant
            ("cafre", ["ca", "fre"]),
            ("aflojar", ["a", "flo", "jar"]),
            # velar consonant with liquid consonant
            ("agrandar", ["a", "gran", "dar"]),
            ("aglutinar", ["a", "glu", "ti", "nar"]),
            ("acróbata", ["a", "cró", "ba", "ta"]),
            ("aclamar", ["a", "cla", "mar"]),
            # dental consonant with aveolar flap consonant
            ("cuadro", ["cua", "dro"]),
            ("cuatro", ["cua", "tro"]),
            # /tl/ at the end of word is a syllable
            ("popocatépetl", ["po", "po", "ca", "té", "pe", "tl"]),
            ("iztaccíhuatl", ["iz", "tac", "cí", "hua", "tl"]),
            ("xicohténcatl", ["xi", "coh", "tén", "ca", "tl"]),
            ("quetzalcóatl", ["quet", "zal", "có", "a", "tl"]),
            # /tl/ is broken within a word
            ("atlas", ["at", "las"]),
            ("atlantico", ["at", "lan", "ti", "co"]),
            # two consonant clusters
            ("inseparable", ["in", "se", "pa", "ra", "ble"]),
            ("artista", ["ar", "tis", "ta"]),
            ("obtener", ["ob", "te", "ner"]),
            ("cuenta", ["cuen", "ta"]),
            ("comedlo", ["co", "med", "lo"]),
            ("ponedla", ["po", "ned", "la"]),
            # three consonant clusters
            ("constancia", ["cons", "tan", "cia"]),
            ("perspectiva", ["pers", "pec", "ti", "va"]),
            ("istmo", ["ist", "mo"]),
            ("constitución", ["cons", "ti", "tu", "ción"]),
            ("instaurar", ["ins", "tau", "rar"]),
            ("obstinado", ["obs", "ti", "na", "do"]),
            ("obstáculo", ["obs", "tá", "cu", "lo"]),
            # three consonant clusters ending with unbreakable pair
            ("empleados", ["em", "ple", "a", "dos"]),
            ("englobar", ["en", "glo", "bar"]),
            ("inflamar", ["in", "fla", "mar"]),
            ("contraer", ["con", "tra", "er"]),
            # four consonant clusters
            ("monstruo", ["mons", "truo"]),
            ("abstracto", ["abs", "trac", "to"]),
            ("construir", ["cons", "truir"]),
            # two strong vowels (hiatus)
            ("aéreo", ["a", "é", "re", "o"]),
            ("pelear", ["pe", "le", "ar"]),
            ("leo", ["le", "o"]),
            # strong vowel with weak vowel (diphthong)
            ("aire", ["ai", "re"]),
            ("europa", ["eu", "ro", "pa"]),
            ("ásia", ["á", "sia"]),
            ("bueno", ["bue", "no"]),
            # two weak vowels (diphthong)
            ("cuidado", ["cui", "da", "do"]),
            ("ruidoso", ["rui", "do", "so"]),
            ("triunfante", ["triun", "fan", "te"]),
            ("ciudad", ["ciu", "dad"]),
            # triphthongs
            ("bioinformática", ["bioin", "for", "má", "ti", "ca"]),
            ("radioisótopo", ["ra", "dioi", "só", "to", "po"]),
            ("asociáis", ["a", "so", "ciáis"]),
            ("buey", ["buey"]),
            # weak vowel with stress (hiatus)
            ("había", ["ha", "bí", "a"]),
            ("país", ["pa", "ís"]),
            ("reúno", ["re", "ú", "no"]),
            ("baúl", ["ba", "úl"]),
        ],
    )
    def test_annotate_syllables(self, text: str, expected_syllables: list[str]) -> None:
        word = AnnotatedString(text)
        annotate_phonemes(word)
        syllables = annotate_syllables(word)

        assert word.get_annotations(Syllable) == syllables

        pos = 0
        for syllable, expected_syllable in zip(
            syllables, expected_syllables, strict=True
        ):
            assert syllable.text == expected_syllable
            assert syllable.start == pos
            assert syllable.stop == pos + len(expected_syllable)
            pos += len(expected_syllable)
