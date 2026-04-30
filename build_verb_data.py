import logging
import time
from typing import cast

from conjugation import RegularConstructionConjugator, RegularFormConjugator
from conjugation_analysis import ConjugationAnalyzer
from corpes import CORPES
from corpes_db import CORPESDB
from dle import DLE
from dle_web import DLEWeb
from export_data import build_export_data
from grammar_model import (
    Element,
    ElementTag,
    Lemma,
    LemmaTag,
    PartOfSpeech,
    Regularity,
    Verb,
    VerbForm,
)
from logging_config import configure_logging
from phonetic_analysis import annotate_phonemes
from resources import artifacts_path, obj_path, resources_path
from spelling_analysis import Homonym, SpellingAnalyzer
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables
from tagged_index import TaggedIndex

_logger = logging.getLogger(__name__)


TOP_LEMMAS_SEARCH_LIMIT = 5_000
TOP_ELEMENTS_FREQ_THRESHOLD = 10


def main(ctx: Context) -> None:
    ctx.index_top_corpes_lemmas()
    ctx.index_top_corpes_elements()

    ctx.index_kofi_verbs()
    ctx.index_dpd_model_verbs()
    ctx.index_dle_model_verbs()

    ctx.index_dle_verb_forms()

    ctx.index_regular_verb_forms()
    ctx.analyze_irregular_verb_form_affixes()

    ctx.index_regular_verb_form_constructions()
    ctx.annotate_irregular_verb_forms()
    ctx.annotate_irregular_verb_form_constructions()

    ctx.analyze_element_phonetics()

    ctx.tag_verb_form_homonym_lemmas()
    ctx.lookup_dle_homonym_lemmas()

    ctx.tag_shared_forms()
    ctx.tag_verb_form_homonym_elements()

    ctx.export_verb_data()


class Context:
    def __init__(self, corpes: CORPES, dle: DLE) -> None:
        self._corpes = corpes
        self._dle = dle
        self._lemma_index = TaggedIndex[LemmaTag, Lemma]()
        self._element_index = TaggedIndex[ElementTag, Element]()
        self._conjugation_analyzer = ConjugationAnalyzer(
            self._lemma_index, self._element_index
        )
        self._spelling_analyzer = SpellingAnalyzer(
            self._lemma_index, self._element_index
        )

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
                continue

            if freq_lemma.part_of_speech is PartOfSpeech.VERB:
                dle_verb = self._dle.get_verb(freq_lemma.tag)
                tagged_lemma = self._lemma_index.setdefault(
                    dle_verb.tag, dle_verb.as_verb()
                )
                if dle_verb.is_model:
                    tagged_lemma.tag(Regularity.MODEL_VERB)

                verb_count += 1
            else:
                tagged_lemma = self._lemma_index.setdefault(
                    freq_lemma.tag, freq_lemma.as_lemma()
                )

            lemma = tagged_lemma.value
            lemma.freq_adj = freq_lemma.freq_adj
            tagged_lemma.tag(*lemma.tags)

            lemma_count += 1

        _logger.info("indexed %d lemmas, %d verbs", lemma_count, verb_count)

    def index_top_corpes_elements(self) -> None:
        _logger.info("indexing top CORPES elements")

        element_count = 0

        non_verb_lemmas = self._lemma_index.lookup()
        non_verb_lemmas -= self._lemma_index.lookup(PartOfSpeech.VERB)
        for tagged_lemma in non_verb_lemmas:
            top_elements = self._corpes.get_top_elements(
                tagged_lemma.key, TOP_ELEMENTS_FREQ_THRESHOLD
            )
            for freq_element in top_elements:
                if not (freq_element.form.isalpha() and freq_element.form.islower()):
                    continue

                tagged_element = self._element_index.setdefault(
                    freq_element.tag, freq_element.as_element(tagged_lemma.value)
                )

                element = tagged_element.value
                tagged_element.tag(*element.tags)

                element_count += 1

        _logger.info("indexed %d elements", element_count)

    def index_dpd_model_verbs(self) -> None:
        _logger.info("indexing DPD model verbs")

        for verb in self._index_verb_list("dpd_model_verbs.txt"):
            tagged_lemma = self._lemma_index[verb.tag]
            if Regularity.MODEL_VERB not in tagged_lemma.tags:
                _logger.info("tagging model verb: %s", verb.tag.base_form)
                tagged_lemma.tag(Regularity.MODEL_VERB)

    def index_kofi_verbs(self) -> None:
        _logger.info("indexing KOFI verbs")

        for i, verb in enumerate(self._index_verb_list("kofi_verbs.txt")):
            verb.study_order = i + 1

    def _index_verb_list(self, list_name: str) -> list[Verb]:
        verb_list = (resources_path / list_name).read_text().splitlines()

        verb_count = 0

        result = []
        for verb_item in verb_list:
            lemma_tag = LemmaTag(verb_item, PartOfSpeech.VERB)
            freq_lemma = self._corpes.get_lemma(lemma_tag)
            dle_verb = self._dle.get_verb(lemma_tag)

            if dle_verb.tag in self._lemma_index:
                result.append(cast("Verb", self._lemma_index[dle_verb.tag].value))
                continue

            tagged_verb = self._lemma_index.setdefault(dle_verb.tag, dle_verb.as_verb())

            verb = cast("Verb", tagged_verb.value)
            verb.freq_adj = freq_lemma.freq_adj
            tagged_verb.tag(*verb.tags)
            if dle_verb.is_model:
                tagged_verb.tag(Regularity.MODEL_VERB)

            result.append(verb)

            verb_count += 1

        _logger.info("indexed %d verbs", verb_count)

        return result

    def index_dle_model_verbs(self) -> None:
        _logger.info("indexing DLE model verbs")

        verb_count = 0

        model_verbs = {
            m
            for v in self._lemma_index.lookup(PartOfSpeech.VERB)
            for m in cast("Verb", v.value).models
        }
        for verb_tag in model_verbs:
            if verb_tag in self._lemma_index:
                continue

            freq_lemma = self._corpes.get_lemma(verb_tag)
            dle_verb = self._dle.get_verb(verb_tag)
            tagged_verb = self._lemma_index.setdefault(verb_tag, dle_verb.as_verb())

            verb = tagged_verb.value
            verb.freq_adj = freq_lemma.freq_adj
            tagged_verb.tag(*verb.tags, Regularity.MODEL_VERB)

            verb_count += 1

        _logger.info("indexed %d verbs", verb_count)

    def index_dle_verb_forms(self) -> None:
        _logger.info("indexing DLE verb forms")

        form_count = 0

        for tagged_verb in self._lemma_index.lookup(PartOfSpeech.VERB):
            verb = cast("Verb", tagged_verb.value)
            for dle_form in self._dle.get_verb_forms(verb.tag):
                tagged_element = self._element_index.setdefault(
                    dle_form.tag, dle_form.as_verb_form(verb)
                )

                form = cast("VerbForm", tagged_element.value)
                tagged_element.tag(*form.tags, Regularity.CORRECT_FORM)

                form_count += 1

        _logger.info("indexed %d verb forms", form_count)

    def index_regular_verb_forms(self) -> None:
        _logger.info("indexing regular verb forms")

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            self._conjugation_analyzer.index_regular_forms(
                cast("VerbForm", tagged_form.value),
                RegularFormConjugator(),
                Regularity.REGULAR_FORM,
            )

    def analyze_irregular_verb_form_affixes(self) -> None:
        _logger.info("analyzing irregular verb form affixes")

        irregular_verb_forms = self._element_index.lookup(Regularity.CORRECT_FORM)
        irregular_verb_forms -= self._element_index.lookup(Regularity.REGULAR_FORM)
        for tagged_form in irregular_verb_forms:
            self._conjugation_analyzer.annotate_irregular_affix(
                cast("VerbForm", tagged_form.value)
            )

    def index_regular_verb_form_constructions(self) -> None:
        _logger.info("indexing regular verb form constructions")

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            self._conjugation_analyzer.index_regular_forms(
                cast("VerbForm", tagged_form.value),
                RegularConstructionConjugator(self._element_index),
                Regularity.REGULAR_CONSTRUCTION,
            )

    def annotate_irregular_verb_forms(self) -> None:
        _logger.info("annotating irregular verb forms")

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            self._conjugation_analyzer.annotate_irregular_form(
                cast("VerbForm", tagged_form.value)
            )

        regular_verbs = self._lemma_index.lookup(PartOfSpeech.VERB)
        regular_verbs -= self._lemma_index.lookup(Regularity.IRREGULAR_VERB)
        for tagged_verb in regular_verbs:
            tagged_verb.tag(Regularity.REGULAR_VERB)

    def annotate_irregular_verb_form_constructions(self) -> None:
        _logger.info("annotating irregular verb form constructions")

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            self._conjugation_analyzer.annotate_irregular_construction(
                cast("VerbForm", tagged_form.value)
            )

    def analyze_element_phonetics(self) -> None:
        _logger.info("analyzing element phonetics")

        for tagged_element in self._element_index.lookup():
            key, element = tagged_element.key, tagged_element.value
            annotate_phonemes(element.annotated_form)
            annotate_syllables(element.annotated_form)
            annotate_stress(element.annotated_form)

            self._spelling_analyzer.tag_phonetic_spelling(key)

    def tag_verb_form_homonym_lemmas(self) -> None:
        _logger.info("tagging verb form homonym lemmas")

        for tagged_form in self._element_index.lookup(PartOfSpeech.VERB):
            self._spelling_analyzer.tag_homonyms_lemmas(tagged_form.key)

    def lookup_dle_homonym_lemmas(self) -> None:
        _logger.info("looking up homonym lemmas in DLE")

        removed_count = 0

        non_verb_homonyms = self._lemma_index.lookup(Homonym.HOMONYM)
        non_verb_homonyms -= self._lemma_index.lookup(PartOfSpeech.VERB)
        for tagged_lemma in non_verb_homonyms:
            dle_lemma = self._dle.get_lemma(tagged_lemma.key)

            if dle_lemma is None:
                self._lemma_index.remove(tagged_lemma.key)
                for tagged_element in self._element_index.lookup(tagged_lemma.key):
                    self._element_index.remove(tagged_element.key)

                removed_count += 1
                continue

            tagged_lemma.value.dle_url = dle_lemma.dle_url

        _logger.info("removed %d lemmas not found in DLE", removed_count)

    def tag_shared_forms(self) -> None:
        _logger.info("tagging shared forms")

        for tagged_element in self._element_index.lookup():
            self._spelling_analyzer.tag_shared_forms(tagged_element.key)

    def tag_verb_form_homonym_elements(self) -> None:
        _logger.info("tagging verb form homonym elements")

        homonym_count = 0

        for tagged_form in self._element_index.lookup(PartOfSpeech.VERB):
            for homonym in self._spelling_analyzer.tag_homonyms(tagged_form.key):
                if homonym.part_of_speech is not PartOfSpeech.VERB:
                    self._spelling_analyzer.tag_homonyms(homonym)
                    homonym_count += 1

        _logger.info("tagged %d verb form homonyms", homonym_count)

    def export_verb_data(self) -> None:
        _logger.info("exporting verb data")

        export_lemmas = self._lemma_index.lookup(PartOfSpeech.VERB)
        export_lemmas |= self._lemma_index.lookup(Homonym.HOMONYM)
        export_elements = self._element_index.lookup(PartOfSpeech.VERB)
        export_elements |= self._element_index.lookup(Homonym.HOMONYM)

        export_data = build_export_data(export_lemmas, export_elements)
        export_json = export_data.model_dump_json(
            ensure_ascii=False, exclude_defaults=True
        )
        (artifacts_path / "verb_data.json").write_text(export_json)

        _logger.info(
            "exported %d lemmas, %d verbs",
            len(export_data.lemmas),
            sum(1 for x in export_data.lemmas if x.part_of_speech is PartOfSpeech.VERB),
        )

        _logger.info(
            "exported %d elements, %d verb forms",
            len(export_data.elements),
            sum(
                1
                for x in export_data.elements
                if x.id.part_of_speech is PartOfSpeech.VERB
            ),
        )


if __name__ == "__main__":
    configure_logging()

    corpes_db = CORPESDB(obj_path / "corpes.db")
    corpes = CORPES(corpes_db)

    dle_web = DLEWeb(cache_dir=obj_path / "dle_web")
    dle = DLE(dle_web, cache_dir=obj_path / "cache")

    start_time = time.perf_counter()

    corpes_db.initialize()
    main(Context(corpes, dle))

    _logger.info("done in %.3fs", time.perf_counter() - start_time)
