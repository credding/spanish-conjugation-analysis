import logging
from contextlib import closing
from dataclasses import InitVar, dataclass, field

import corpes_db
from corpes_tag import ClassTag, Tag
from grammar_model import Class, Element, Lemma

_logger = logging.getLogger(__name__)


@dataclass
class FreqElement:
    form: str
    lemma: str
    tag_str: InitVar[str]
    tag: Tag = field(init=False)
    freq: int
    freq_norm_with_punc: float
    freq_norm_without_punc: float

    def __post_init__(self, tag_str: str):
        self.tag = Tag(tag_str)

    @property
    def class_(self) -> Class:
        return self.tag.class_tag.class_

    def as_element(self) -> Element:
        return Element(self.form, Lemma(self.lemma, self.class_))


@dataclass
class FreqLemma:
    lemma: str
    class_str: InitVar[str]
    class_tag: ClassTag = field(init=False)
    freq: int
    freq_norm_with_punc: float
    freq_norm_without_punc: float

    def __post_init__(self, class_str: str):
        self.class_tag = ClassTag(class_str)

    @property
    def class_(self) -> Class:
        return self.class_tag.class_

    def as_lemma(self) -> Lemma:
        return Lemma(self.lemma, self.class_)


@dataclass
class FreqForm:
    form: str
    freq: int
    freq_norm: float


@dataclass
class DpLemma:
    lemma: str
    class_str: InitVar[str]
    class_tag: ClassTag = field(init=False)
    freq: int
    freq_norm: float
    dp: float
    num_countries: int
    freq_adj: float

    def __post_init__(self, class_str: str):
        self.class_tag = ClassTag(class_str)

    @property
    def class_(self) -> Class:
        return self.class_tag.class_

    def as_lemma(self) -> Lemma:
        return Lemma(self.lemma, self.class_)


class CORPES:
    def __init__(self):
        corpes_db.initialize()

        self._conn = corpes_db.connect()

    def get_top_lemmas_by_freq_adj(self, n: int | None = None) -> list[DpLemma]:
        limit_clause = ""
        parameters = ()
        if n is not None:
            limit_clause = " LIMIT ?"
            parameters = (n,)

        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT lemma, class AS class_str, freq, freq_norm, dp, num_countries, freq_adj "
                "FROM dp_lemmas "
                f"ORDER BY freq_adj DESC {limit_clause};",
                parameters,
            )
            return [DpLemma(**x) for x in cur]

    def get_top_elements_by_lemma_freq_adj(
        self, n: int | None = None
    ) -> list[FreqElement]:
        limit_clause = ""
        parameters = ()
        if n is not None:
            limit_clause = "LIMIT ? "
            parameters = (n,)

        with closing(self._conn.cursor()) as cur:
            cur.execute(
                f"WITH top_dp_lemmas AS (SELECT lemma, class FROM dp_lemmas ORDER BY freq_adj DESC {limit_clause})"
                "SELECT e.form, e.lemma, e.tag as tag_str, e.freq, e.freq_norm_with_punc, e.freq_norm_without_punc "
                "FROM freq_elements e "
                "JOIN top_dp_lemmas l ON e.lemma = l.lemma AND e.tag LIKE l.class || '%'"
                "ORDER BY e.id;",
                parameters,
            )
            return [FreqElement(**x) for x in cur]

    def get_infinitive_element(self, lemma: Lemma) -> FreqElement:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT lemma, form, tag as tag_str, freq, freq_norm_with_punc, freq_norm_without_punc FROM freq_elements "
                "WHERE form = ? "
                "AND tag LIKE 'V____v%' "  # only match infinitive forms
                "ORDER BY id;",
                (lemma.base_form,),
            )
            return FreqElement(**cur.fetchone())

    def get_dp_lemma(self, lemma: Lemma) -> DpLemma | None:
        with closing(self._conn.cursor()) as cur:
            cur.execute(
                "SELECT lemma, class AS class_str, freq, freq_norm, dp, num_countries, freq_adj FROM dp_lemmas "
                "WHERE (lemma, class) = (?, ?) "
                "ORDER BY freq_adj DESC;",
                (lemma.base_form, lemma.class_),
            )
            row = cur.fetchone()
            return DpLemma(**row) if row else None
