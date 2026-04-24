from contextlib import closing

import corpes_db
from corpes_model import DpLemma, FreqElement
from grammar_model import Lemma


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
