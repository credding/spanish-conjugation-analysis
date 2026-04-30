from contextlib import closing

from corpes_db import CORPESDB
from corpes_model import FreqElement, FreqLemma
from grammar_model import LemmaTag, PartOfSpeech

_PARTS_OF_SPEECH: dict[str, PartOfSpeech] = {
    "A": PartOfSpeech.ADJECTIVE,
    "R": PartOfSpeech.ADVERB,
    "J": PartOfSpeech.AFFIX,
    "T": PartOfSpeech.ARTICLE,
    "C": PartOfSpeech.CONJUNCTION,
    "E": PartOfSpeech.CONTRACTION,
    "Q": PartOfSpeech.QUANTIFIER,
    "D": PartOfSpeech.DEMONSTRATIVE,
    "U": PartOfSpeech.UNKNOWN,
    "F": PartOfSpeech.FOREIGN,
    "I": PartOfSpeech.INTERJECTION,
    "W": PartOfSpeech.INTERROGATIVE,
    "M": PartOfSpeech.NUMERAL,
    "X": PartOfSpeech.POSSESSIVE,
    "P": PartOfSpeech.PREPOSITION,
    "L": PartOfSpeech.PERSONAL_PRONOUN,
    "Y": PartOfSpeech.PUNCTUATION,
    "H": PartOfSpeech.RELATIVE,
    "N": PartOfSpeech.NOUN,
    "V": PartOfSpeech.VERB,
}
_PARTS_OF_SPEECH_INV = {v: k for k, v in _PARTS_OF_SPEECH.items()}


class CORPES:
    def __init__(self, corpes_db: CORPESDB) -> None:
        self._conn = corpes_db.connect()

    def get_top_lemmas_by_freq_adj(self, n: int = -1) -> list[FreqLemma]:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT lemma, class, freq_adj FROM dp_lemmas "
                "ORDER BY freq_adj DESC LIMIT ?;",
                (n,),
            )
            return [_map_lemma(x) for x in cur]

    def get_top_elements(
        self, lemma_tag: LemmaTag, gt_freq: int = 0
    ) -> list[FreqElement]:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT form, lemma, tag FROM freq_elements "
                "WHERE lemma = ? AND tag LIKE ? || '%' AND freq_norm_without_punc > ? "
                "ORDER BY id;",
                (
                    lemma_tag.base_form,
                    _PARTS_OF_SPEECH_INV[lemma_tag.part_of_speech],
                    gt_freq,
                ),
            )
            return [_map_element(x) for x in cur]

    def get_lemma(self, lemma_tag: LemmaTag) -> FreqLemma:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT lemma, class, freq_adj FROM dp_lemmas "
                "WHERE (lemma, class) = (?, ?);",
                (lemma_tag.base_form, _PARTS_OF_SPEECH_INV[lemma_tag.part_of_speech]),
            )
            return _map_lemma(cur.fetchone())


def _map_lemma(row: dict) -> FreqLemma:
    return FreqLemma(row["lemma"], _PARTS_OF_SPEECH[row["class"]], row["freq_adj"])


def _map_element(row: dict) -> FreqElement:
    return FreqElement(
        LemmaTag(row["lemma"], _PARTS_OF_SPEECH[row["tag"][0]]), row["form"]
    )
