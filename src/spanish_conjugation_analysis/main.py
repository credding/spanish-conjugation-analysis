# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import time

from spanish_grammar import PartOfSpeech, Verb

from .conjugation_analysis import ConjugationAnalyzer, Regularity
from .corpes import CORPES
from .corpes_db import CORPESDB
from .corpes_model import FreqLemma
from .dle import DLE
from .dle_web import DLEWeb
from .export_data import build_export_data
from .grammar_index import GrammarIndex, TaggedVerb
from .grammar_index_model import IndexElement, IndexLemma, IndexVerb, IndexVerbForm
from .homonymy_analysis import Homonymy, HomonymyAnalyzer
from .logging_config import configure_logging
from .resources import artifacts_path, obj_path, resources_path

_logger = logging.getLogger(__name__)


TOP_LEMMAS_SEARCH_LIMIT = 5_000
TOP_ELEMENTS_FREQ_THRESHOLD = 10


def main() -> None:
    configure_logging()

    start_time = time.perf_counter()

    corpes_db = CORPESDB(obj_path / "corpes.db")
    corpes_db.initialize()
    corpes = CORPES(corpes_db)

    dle_web = DLEWeb(cache_dir=obj_path / "dle_web")
    dle = DLE(dle_web, cache_dir=obj_path / "cache")

    ctx = Context(corpes, dle)

    ctx.index_top_corpes_lemmas()
    ctx.index_top_corpes_elements()

    ctx.index_kofi_verbs()
    ctx.index_dpd_model_verbs()
    ctx.index_dle_model_verbs()

    ctx.index_dle_verb_forms()
    ctx.index_regular_verb_forms()

    ctx.annotate_verb_form_regular_spelling_changes()
    ctx.annotate_verb_form_irregularities()
    ctx.tag_verb_regularity()

    ctx.lookup_dle_verb_form_homonym_lemmas()
    ctx.tag_homonyms()

    ctx.export_verb_data()

    _logger.info("done in %.3fs", time.perf_counter() - start_time)


class Context:
    def __init__(self, corpes: CORPES, dle: DLE) -> None:
        self._corpes = corpes
        self._dle = dle

        self._grammar_index = GrammarIndex()

        self._conjug_analyzer = ConjugationAnalyzer(self._grammar_index)
        self._homonymy_analyzer = HomonymyAnalyzer(self._grammar_index)

    def index_top_corpes_lemmas(self) -> None:
        _logger.info("indexing top CORPES lemmas")

        lemma_count = 0
        verb_count = 0

        top_lemmas = self._corpes.get_top_lemmas_by_freq_adj(TOP_LEMMAS_SEARCH_LIMIT)
        for freq_lemma in top_lemmas:
            if (
                freq_lemma.part_of_speech is PartOfSpeech.NOUN
                and len(freq_lemma.base_form) == 1
            ):
                # skip alphabet letters: 'a', 'b', 'c', etc.
                continue

            if freq_lemma.part_of_speech is PartOfSpeech.VERB:
                self._index_freq_lemma_verb(freq_lemma)
                verb_count += 1
            else:
                self._grammar_index.index_lemma(
                    IndexLemma(
                        lemma_tag=freq_lemma.lemma_tag,
                        dle_url="",
                        freq_adj=freq_lemma.freq_adj,
                    )
                )

            lemma_count += 1

        _logger.info("indexed %d lemma(s), %d verb(s)", lemma_count, verb_count)

    def _index_freq_lemma_verb(self, freq_lemma: FreqLemma) -> TaggedVerb:
        dle_verb = self._dle.get_verb(Verb(freq_lemma.base_form))

        verb = self._grammar_index.index_verb(
            IndexVerb(
                lemma_tag=dle_verb.lemma_tag,
                dle_url=dle_verb.dle_url,
                freq_adj=freq_lemma.freq_adj,
                model_verbs=dle_verb.model_verbs,
                study_order=None,
            )
        )

        if dle_verb.is_model_verb:
            verb.tag(Regularity.MODEL_VERB)

        return verb

    def _index_verb(self, verb: Verb) -> TaggedVerb:
        freq_lemma = self._corpes.get_lemma(verb)
        return self._index_freq_lemma_verb(freq_lemma)

    def index_top_corpes_elements(self) -> None:
        _logger.info("indexing top CORPES elements")

        top_elements = [
            ex
            for lx in self._grammar_index.lookup_lemmas()
            if lx.value.part_of_speech is not PartOfSpeech.VERB
            for ex in self._corpes.get_top_elements(lx.key, TOP_ELEMENTS_FREQ_THRESHOLD)
            if ex.form.isalpha() and ex.form.islower()
        ]
        for freq_element in top_elements:
            element = self._grammar_index.index_element(
                IndexElement(element_tag=freq_element.element_tag)
            )
            element.tag(Regularity.CORRECT_FORM)

        _logger.info("indexed %d element(s)", len(top_elements))

    def index_dpd_model_verbs(self) -> None:
        _logger.info("indexing DPD model verbs")

        for verb in self._index_verb_list("dpd_model_verbs.txt"):
            if Regularity.MODEL_VERB not in verb.tags:
                _logger.info("tagging model verb: %s", verb.value.base_form)
                verb.tag(Regularity.MODEL_VERB)

    def index_kofi_verbs(self) -> None:
        _logger.info("indexing KOFI verbs")

        for i, verb in enumerate(self._index_verb_list("kofi_verbs.txt")):
            verb.value.study_order = i + 1

    def _index_verb_list(self, list_name: str) -> list[TaggedVerb]:
        result: list[TaggedVerb] = [
            self._index_verb(Verb(base_form))
            for base_form in (resources_path / list_name).read_text().splitlines()
            if not base_form.startswith("#")
        ]

        _logger.info("indexed %d verb(s)", len(result))

        return result

    def index_dle_model_verbs(self) -> None:
        _logger.info("indexing DLE model verbs")

        model_verbs = {
            mx
            for vx in self._grammar_index.lookup_verbs()
            for mx in vx.value.model_verbs
        }
        for verb in model_verbs:
            self._index_verb(verb)

        _logger.info("indexed %d verb(s)", len(model_verbs))

    def index_dle_verb_forms(self) -> None:
        _logger.info("indexing DLE verb forms")

        dle_forms = [
            fx
            for vx in self._grammar_index.lookup_verbs()
            for fx in self._dle.get_verb_forms(vx.key)
        ]
        for dle_form in dle_forms:
            form = self._grammar_index.index_verb_form(
                IndexVerbForm(
                    element_tag=dle_form.element_tag,
                    preference=dle_form.preference,
                    alt_phonology=None,
                )
            )
            form.tag(Regularity.CORRECT_FORM)

        _logger.info("indexed %d verb form(s)", len(dle_forms))

    def index_regular_verb_forms(self) -> None:
        _logger.info("indexing regular verb forms")

        count = 0
        for form in self._grammar_index.lookup_verb_forms(Regularity.CORRECT_FORM):
            count += self._conjug_analyzer.index_regular_verb_forms(form)

        _logger.info("indexed %d verb form(s)", count)

    def annotate_verb_form_regular_spelling_changes(self) -> None:
        _logger.info("annotating verb form regular spelling changes")

        for form in self._grammar_index.lookup_verb_forms(
            Regularity.REGULAR_MORPHOLOGY
        ):
            self._conjug_analyzer.annotate_regular_spelling_change(form)

    def annotate_verb_form_irregularities(self) -> None:
        _logger.info("annotating verb form irregularities")

        for form in self._grammar_index.lookup_verb_forms(Regularity.CORRECT_FORM):
            self._conjug_analyzer.annotate_form_irregularities(form)

    def tag_verb_regularity(self) -> None:
        _logger.info("tagging verb regularity")

        for verb in self._grammar_index.lookup_verbs():
            self._conjug_analyzer.tag_verb_regularity(verb)

    def lookup_dle_verb_form_homonym_lemmas(self) -> None:
        _logger.info("looking up verb form homonym lemmas in DLE")

        removed_count = 0

        homonym_lemma_tags = {
            ex.value.lemma_tag
            for fx in self._grammar_index.lookup_verb_forms()
            for ex in self._grammar_index.lookup_elements(
                fx.value.phonetic_form_no_stress
            )
            if ex.value.part_of_speech is not PartOfSpeech.VERB
        }
        for lemma_tag in homonym_lemma_tags:
            dle_lemma = self._dle.get_lemma(lemma_tag)
            if dle_lemma is None:
                del self._grammar_index.lemmas[lemma_tag]
                for element in self._grammar_index.lookup_elements(lemma_tag):
                    del self._grammar_index.elements[element.key]

                removed_count += 1
                continue

            lemma = self._grammar_index.lemmas[lemma_tag]
            lemma.value.dle_url = dle_lemma.dle_url

        _logger.info("removed %d lemma(s) not found in DLE", removed_count)

    def tag_homonyms(self) -> None:
        _logger.info("tagging homonyms")

        for form in self._grammar_index.lookup_elements(PartOfSpeech.VERB):
            self._homonymy_analyzer.tag_heteronymous_forms(form)
            self._homonymy_analyzer.tag_shared_forms(form)

            for homonym in self._homonymy_analyzer.tag_homonyms(form):
                if homonym.value.part_of_speech is not PartOfSpeech.VERB:
                    self._homonymy_analyzer.tag_homonyms(homonym)

    def export_verb_data(self) -> None:
        _logger.info("exporting verb data")

        verbs = self._grammar_index.lookup_lemmas(PartOfSpeech.VERB)
        lemmas = verbs | self._grammar_index.lookup_lemmas(Homonymy.HOMONYM)
        verb_forms = self._grammar_index.lookup_elements(PartOfSpeech.VERB)
        elements = verb_forms | self._grammar_index.lookup_elements(Homonymy.HOMONYM)

        export_data = build_export_data(lemmas, elements)
        export_json = export_data.model_dump_json(
            ensure_ascii=False, exclude_defaults=True
        )
        export_bytes = export_json.encode()
        (artifacts_path / "verb_data.json").write_bytes(export_bytes)

        _logger.info("exported %d lemma(s), %d verb(s)", len(lemmas), len(verbs))
        _logger.info(
            "exported %d element(s), %d verb form(s)", len(elements), len(verb_forms)
        )
