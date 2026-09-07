# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import logging
import time
from pathlib import Path

from spanish_grammar import Lemma, PartOfSpeech, Verb

from spanish_conjugation_analysis.corpes_model import FreqLemma

from .corpes import CORPES
from .corpes_db import CORPESDB
from .dle import DLE
from .dle_model import DLELemma, DLEVerb, DLEVerbForm
from .dle_web import DLEWeb
from .language_data import (
    TOP_LEMMAS_SEARCH_LIMIT,
    write_dle_lemmas,
    write_dle_verb_forms,
)
from .logging_config import configure_logging
from .resources import obj_path
from .verb_list import get_verb_list

_logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("outdir", type=Path)

    args = parser.parse_args()
    outdir: Path = args.outdir

    configure_logging()

    start_time = time.perf_counter()

    corpes_db = CORPESDB(obj_path / "corpes.db")
    corpes_db.initialize()
    corpes = CORPES(corpes_db)

    dle_web = DLEWeb(cache_dir=obj_path / "dle_web")
    dle = DLE(dle_web)

    ctx = Context(dle)

    for freq_lemma in corpes.get_top_lemmas_by_freq_adj(TOP_LEMMAS_SEARCH_LIMIT):
        ctx.scrape_lemma(freq_lemma)

    for verb in get_verb_list("kofi_verbs.txt"):
        ctx.scrape_model_verb(verb)

    for verb in get_verb_list("dpd_model_verbs.txt"):
        ctx.scrape_model_verb(verb)

    for verb in ctx.dle_model_verbs:
        ctx.scrape_model_verb(verb)

    write_dle_lemmas(outdir, ctx.dle_lemmas)
    write_dle_verb_forms(outdir, ctx.dle_verb_forms)

    _logger.info("done in %.3fs", time.perf_counter() - start_time)


class Context:
    def __init__(self, dle: DLE) -> None:
        self._dle = dle

        self.dle_lemmas: dict[Lemma, DLELemma] = {}
        self.dle_verb_forms: dict[Verb, list[DLEVerbForm]] = {}
        self.dle_model_verbs: set[Verb] = set()

    def scrape_lemma(self, freq_lemma: FreqLemma) -> None:
        if not all(x.isalpha() for x in freq_lemma.base_form):
            return

        dle_lemma = self._dle.get_lemma(freq_lemma.lemma_tag)
        if dle_lemma is None:
            return

        if freq_lemma.part_of_speech is PartOfSpeech.VERB:
            lemma = Verb(freq_lemma.base_form)
        else:
            lemma = freq_lemma.lemma_tag

        self.dle_lemmas[lemma] = dle_lemma
        self.dle_lemmas[dle_lemma.lemma_tag] = dle_lemma

        if isinstance(dle_lemma, DLEVerb):
            self.dle_model_verbs.update(dle_lemma.model_verbs)

            verb_forms = self._dle.get_verb_forms(dle_lemma.lemma_tag)
            self.dle_verb_forms[dle_lemma.lemma_tag] = verb_forms

    def scrape_model_verb(self, verb: Verb) -> None:
        if verb in self.dle_lemmas:
            return

        dle_verb = self._dle.get_verb(verb)
        self.dle_lemmas[verb] = dle_verb
        self.dle_lemmas[dle_verb.lemma_tag] = dle_verb

        self.dle_model_verbs.update(dle_verb.model_verbs)

        verb_forms = self._dle.get_verb_forms(dle_verb.lemma_tag)
        self.dle_verb_forms[dle_verb.lemma_tag] = verb_forms


if __name__ == "__main__":
    main()
