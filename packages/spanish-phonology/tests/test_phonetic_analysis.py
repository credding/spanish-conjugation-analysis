import string
from collections.abc import Callable

import pytest
from annotated_string import AnnotatedString
from spanish_phonology import Phoneme, PhonemeKind, annotate_phoneme, annotate_phonemes

SIMPLE_VOWEL = set("aeiouáéíóúü")
VOWEL = SIMPLE_VOWEL | {"h" + c for c in SIMPLE_VOWEL}
SOFT_VOWEL = set("eiéí") | {"h" + c for c in "eiéí"}
ALPHABET = {*string.ascii_lowercase, *VOWEL, "ñ", "ch", "ll", "rr", ""}
HARD_VOWEL = ALPHABET - SOFT_VOWEL


@pytest.fixture(params=ALPHABET)
def alphabet(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=SOFT_VOWEL)
def soft_vowel(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(params=HARD_VOWEL)
def hard_vowel(request: pytest.FixtureRequest) -> str:
    return request.param


def first_phoneme(text: str) -> Phoneme:
    word = AnnotatedString(text)
    phoneme = annotate_phoneme(word, 0)
    assert phoneme is not None
    assert [*word.annotations] == [phoneme]
    return phoneme


def consecutive_phoneme(text: str) -> Phoneme:
    word = AnnotatedString("_" + text)
    phoneme = annotate_phoneme(word, 1)
    assert phoneme is not None
    assert [*word.annotations] == [phoneme]
    return phoneme


@pytest.fixture(params=[first_phoneme, consecutive_phoneme])
def phoneme_position(request: pytest.FixtureRequest) -> Callable[[str], Phoneme]:
    return request.param


def assert_phoneme_annotation(
    phoneme: Phoneme,
    expected_text: str,
    expected_phoneme_kind: PhonemeKind,
    expected_phoneme: str,
) -> None:
    assert phoneme.text == expected_text
    assert phoneme.phoneme_kind is expected_phoneme_kind
    assert phoneme.phoneme == expected_phoneme


class TestAnnotatePhoneme:
    def test_empty(self) -> None:
        word = AnnotatedString("")
        phonemes = annotate_phonemes(word)
        assert [*word.annotations] == phonemes
        assert phonemes == []

    @pytest.mark.parametrize(
        ("text", "expected_phoneme"),
        [
            ("b", "b"),
            # c can form a compound consonant
            # c sound has hard/soft variation
            ("d", "d"),
            ("f", "f"),
            # g sound has hard/soft variation
            # h before a vowel is silent
            ("j", "x"),  # j sounds like 'x'
            ("k", "k"),
            # l can form a compound consonant
            ("m", "m"),
            ("n", "n"),
            ("ñ", "ñ"),
            ("p", "p"),
            ("q", "k"),  # q sounds like 'k'
            # r can form a compound consonant
            # r sound is different at start of word
            ("s", "s"),
            ("t", "t"),
            ("v", "b"),  # v sounds like 'b'
            ("w", "w"),
            # x sound is different at start of word
            ("y", "y"),
            ("z", "s"),  # z sounds like 's'
            # compound consonants
            ("ch", "ch"),
            ("ll", "y"),
            ("rr", "rr"),
        ],
    )
    def test_consonant(
        self,
        text: str,
        alphabet: str,
        phoneme_position: Callable[[str], Phoneme],
        expected_phoneme: str,
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position(text + alphabet),
            text,
            PhonemeKind.CONSONANT,
            expected_phoneme,
        )

    @pytest.mark.parametrize("next_char", ALPHABET - SIMPLE_VOWEL)
    def test_consonant_h(
        self, next_char: str, phoneme_position: Callable[[str], Phoneme]
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position("h" + next_char), "h", PhonemeKind.CONSONANT, "h"
        )

    @pytest.mark.parametrize(
        "next_char", [c for c in ALPHABET if not c.startswith("l")]
    )
    def test_consonant_l(
        self, next_char: str, phoneme_position: Callable[[str], Phoneme]
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position("l" + next_char), "l", PhonemeKind.CONSONANT, "l"
        )

    @pytest.mark.parametrize(("text", "expected_phoneme"), [("x", "s")])
    def test_first_consonant(
        self, text: str, alphabet: str, expected_phoneme: str
    ) -> None:
        assert_phoneme_annotation(
            first_phoneme(text + alphabet),
            text,
            PhonemeKind.CONSONANT,
            expected_phoneme,
        )

    @pytest.mark.parametrize(("text", "expected_phoneme"), [("x", "x")])
    def test_consecutive_consonant(
        self, text: str, alphabet: str, expected_phoneme: str
    ) -> None:
        assert_phoneme_annotation(
            consecutive_phoneme(text + alphabet),
            text,
            PhonemeKind.CONSONANT,
            expected_phoneme,
        )

    @pytest.mark.parametrize(
        "next_char", [c for c in ALPHABET if not c.startswith("r")]
    )
    def test_first_consonant_r(self, next_char: str) -> None:
        assert_phoneme_annotation(
            first_phoneme("r" + next_char), "r", PhonemeKind.CONSONANT, "rr"
        )

    @pytest.mark.parametrize(
        "next_char", [c for c in ALPHABET if not c.startswith("r")]
    )
    def test_consecutive_consonant_r(self, next_char: str) -> None:
        assert_phoneme_annotation(
            consecutive_phoneme("r" + next_char), "r", PhonemeKind.CONSONANT, "r"
        )

    @pytest.mark.parametrize(("text", "expected_phoneme"), [("g", "g")])
    def test_consonant_plus_hard_vowel(
        self,
        text: str,
        hard_vowel: str,
        phoneme_position: Callable[[str], Phoneme],
        expected_phoneme: str,
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position(text + hard_vowel),
            text,
            PhonemeKind.CONSONANT,
            expected_phoneme,
        )

    @pytest.mark.parametrize(
        ("text", "expected_phoneme"), [("g", "x"), ("qu", "k"), ("gu", "g")]
    )
    def test_consonant_plus_soft_vowel(
        self,
        text: str,
        soft_vowel: str,
        phoneme_position: Callable[[str], Phoneme],
        expected_phoneme: str,
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position(text + soft_vowel),
            text,
            PhonemeKind.CONSONANT,
            expected_phoneme,
        )

    @pytest.mark.parametrize(
        "next_char", [c for c in HARD_VOWEL if not c.startswith("h")]
    )
    def test_consonant_c_plus_hard_vowel(
        self, next_char: str, phoneme_position: Callable[[str], Phoneme]
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position("c" + next_char), "c", PhonemeKind.CONSONANT, "k"
        )

    @pytest.mark.parametrize(
        "next_char", [c for c in SOFT_VOWEL if not c.startswith("h")]
    )
    def test_consonant_c_plus_soft_vowel(
        self, next_char: str, phoneme_position: Callable[[str], Phoneme]
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position("c" + next_char), "c", PhonemeKind.CONSONANT, "s"
        )

    @pytest.mark.parametrize(
        ("text", "expected_phoneme"),
        [
            ("a", "a"),
            ("e", "e"),
            ("o", "o"),
            # stressed vowels are strong
            ("á", "a"),
            ("é", "e"),
            ("í", "i"),
            ("ó", "o"),
            ("ú", "u"),
            # h is silent, forming a "compound" vowel
            ("ha", "a"),
            ("he", "e"),
            ("ho", "o"),
            # stressed vowels are strong
            ("há", "a"),
            ("hé", "e"),
            ("hí", "i"),
            ("hó", "o"),
            ("hú", "u"),
        ],
    )
    def test_strong_vowel(
        self,
        text: str,
        alphabet: str,
        phoneme_position: Callable[[str], Phoneme],
        expected_phoneme: str,
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position(text + alphabet),
            text,
            PhonemeKind.STRONG_VOWEL,
            expected_phoneme,
        )

    @pytest.mark.parametrize(
        ("text", "expected_phoneme"),
        [
            ("i", "i"),
            ("u", "u"),
            ("ü", "u"),
            # h is silent, forming a "compound" vowel
            ("hi", "i"),
            ("hu", "u"),
            ("hü", "u"),
        ],
    )
    def test_weak_vowel(
        self,
        text: str,
        alphabet: str,
        phoneme_position: Callable[[str], Phoneme],
        expected_phoneme: str,
    ) -> None:
        assert_phoneme_annotation(
            phoneme_position(text + alphabet),
            text,
            PhonemeKind.WEAK_VOWEL,
            expected_phoneme,
        )
