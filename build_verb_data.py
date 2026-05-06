import logging
import time
from typing import cast

from affix_analysis import annotate_affix
from conjugation_analysis import ConjugationAnalyzer
from corpes import CORPES
from corpes_db import CORPESDB
from corpes_model import FreqLemma
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
from spelling_analysis import Homonym, SpellingAnalyzer, build_phonetic_spelling_tags
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables
from tagged_index import TaggedIndex, TaggedItem

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

    ctx.annotate_verb_form_regular_spelling_changes()
    ctx.annotate_verb_form_irregularities()
    ctx.tag_regular_verb_form_spelling()
    ctx.tag_verb_regularity()

    ctx.analyze_element_phonology()

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
        self._regularity_analyzer = ConjugationAnalyzer(
            self._lemma_index, self._element_index
        )
        self._spelling_analyzer = SpellingAnalyzer(
            self._lemma_index, self._element_index
        )

    def _index_lemma(self, lemma: Lemma) -> TaggedItem[LemmaTag, Lemma]:
        tagged_lemma = self._lemma_index.index(lemma.lemma_tag, lemma)
        tagged_lemma.tag(*lemma.tags)

        return tagged_lemma

    def _index_element(self, element: Element) -> TaggedItem[ElementTag, Element]:
        tagged_element = self._element_index.index(element.element_tag, element)
        tagged_element.tag(*element.tags)

        annotate_phonemes(element.annotated_form)
        annotate_syllables(element.annotated_form)
        annotate_stress(element.annotated_form)

        return tagged_element

    def _index_verb_form(self, form: VerbForm) -> TaggedItem[ElementTag, Element]:
        tagged_form = self._index_element(form)

        annotate_affix(
            form.annotated_form, form.lemma_tag, form.tense, form.subject, form.variant
        )

        return tagged_form

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
                self._index_lemma(freq_lemma.as_lemma())

            lemma_count += 1

        _logger.info("indexed %d lemma(s), %d verb(s)", lemma_count, verb_count)

    def _index_freq_lemma_verb(self, freq_lemma: FreqLemma) -> None:
        dle_verb = self._dle.get_verb(freq_lemma.lemma_tag)

        verb = dle_verb.as_verb()
        verb.freq_adj = freq_lemma.freq_adj

        tagged_verb = self._index_lemma(verb)
        if dle_verb.is_model:
            tagged_verb.tag(Regularity.MODEL_VERB)

    def index_top_corpes_elements(self) -> None:
        _logger.info("indexing top CORPES elements")

        element_count = 0

        non_verb_lemmas = set(self._lemma_index.values())
        non_verb_lemmas -= self._lemma_index.lookup(PartOfSpeech.VERB)
        for tagged_lemma in non_verb_lemmas:
            top_elements = self._corpes.get_top_elements(
                tagged_lemma.key, TOP_ELEMENTS_FREQ_THRESHOLD
            )
            for freq_element in top_elements:
                if not (freq_element.form.isalpha() and freq_element.form.islower()):
                    continue

                if freq_element.element_tag in self._element_index:
                    continue

                element = freq_element.as_element(tagged_lemma.value)
                self._index_element(element)

                element_count += 1

        _logger.info("indexed %d element(s)", element_count)

    def index_dpd_model_verbs(self) -> None:
        _logger.info("indexing DPD model verbs")

        for verb in self._index_verb_list("dpd_model_verbs.txt"):
            tagged_lemma = self._lemma_index[verb.lemma_tag]
            if Regularity.MODEL_VERB not in tagged_lemma.tags:
                _logger.info("tagging model verb: %s", verb.lemma_tag.base_form)
                tagged_lemma.tag(Regularity.MODEL_VERB)

    def index_kofi_verbs(self) -> None:
        _logger.info("indexing KOFI verbs")

        for i, verb in enumerate(self._index_verb_list("kofi_verbs.txt")):
            verb.study_order = i + 1

    def _index_verb_list(self, list_name: str) -> list[Verb]:
        verb_list = (resources_path / list_name).read_text().splitlines()

        new_count = 0

        result: list[Verb] = []
        for verb_item in verb_list:
            lemma_tag = LemmaTag(verb_item, PartOfSpeech.VERB)
            freq_lemma = self._corpes.get_lemma(lemma_tag)
            dle_verb = self._dle.get_verb(lemma_tag)

            if dle_verb.lemma_tag in self._lemma_index:
                tagged_verb = self._lemma_index[dle_verb.lemma_tag]
                result.append(cast("Verb", tagged_verb.value))
                continue

            verb = dle_verb.as_verb()
            verb.freq_adj = freq_lemma.freq_adj

            tagged_verb = self._index_lemma(verb)
            if dle_verb.is_model:
                tagged_verb.tag(Regularity.MODEL_VERB)

            result.append(verb)

            new_count += 1

        _logger.info("indexed %d verb(s), %d new", len(verb_list), new_count)

        return result

    def index_dle_model_verbs(self) -> None:
        _logger.info("indexing DLE model verbs")

        new_count = 0

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

            verb = dle_verb.as_verb()
            verb.freq_adj = freq_lemma.freq_adj

            tagged_verb = self._index_lemma(verb)
            tagged_verb.tag(Regularity.MODEL_VERB)

            new_count += 1

        _logger.info("indexed %d verb(s), %d new", len(model_verbs), new_count)

    def index_dle_verb_forms(self) -> None:
        _logger.info("indexing DLE verb forms")

        form_count = 0

        for tagged_verb in self._lemma_index.lookup(PartOfSpeech.VERB):
            verb = cast("Verb", tagged_verb.value)
            for dle_form in self._dle.get_verb_forms(verb.lemma_tag):
                form = dle_form.as_verb_form(verb)
                tagged_form = self._index_verb_form(form)
                tagged_form.tag(Regularity.CORRECT_FORM)

                form_count += 1

        _logger.info("indexed %d verb form(s)", form_count)

    def index_regular_verb_forms(self) -> None:
        _logger.info("indexing regular verb forms")

        form_count = 0

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            form = cast("VerbForm", tagged_form.value)
            form_count += self._regularity_analyzer.index_regular_forms(form)

        _logger.info("indexed %d verb form(s)", form_count)

    def annotate_verb_form_regular_spelling_changes(self) -> None:
        _logger.info("annotating verb form regular spelling changes")

        for tagged_form in self._element_index.lookup(Regularity.REGULAR_MORPHOLOGY):
            form = cast("VerbForm", tagged_form.value)
            self._regularity_analyzer.annotate_regular_spelling_changes(form)

    def annotate_verb_form_irregularities(self) -> None:
        _logger.info("annotating verb form irregularities")

        for tagged_form in self._element_index.lookup(Regularity.CORRECT_FORM):
            form = cast("VerbForm", tagged_form.value)
            self._regularity_analyzer.annotate_form_irregularities(form)

    def tag_regular_verb_form_spelling(self) -> None:
        _logger.info("tagging regular verb form spelling")

        regular_spelling = self._element_index.lookup(Regularity.CORRECT_FORM)
        regular_spelling -= self._element_index.lookup(Regularity.IRREGULAR_SPELLING)
        for tagged_form in regular_spelling:
            tagged_form.tag(Regularity.REGULAR_SPELLING)

    def tag_verb_regularity(self) -> None:
        _logger.info("tagging verb regularity")

        for tagged_verb in self._lemma_index.lookup(PartOfSpeech.VERB):
            form_tags = {
                t for f in self._element_index.lookup(tagged_verb.key) for t in f.tags
            }

            tagged_verb.tag(
                Regularity.IRREGULAR_MORPHOLOGY
                if Regularity.IRREGULAR_MORPHOLOGY in form_tags
                else Regularity.REGULAR_MORPHOLOGY
            )
            tagged_verb.tag(
                Regularity.IRREGULAR_SPELLING
                if Regularity.IRREGULAR_SPELLING in form_tags
                else Regularity.REGULAR_SPELLING
            )
            tagged_verb.tag(
                Regularity.IRREGULAR_CONSTRUCTION
                if Regularity.IRREGULAR_CONSTRUCTION in form_tags
                else Regularity.REGULAR_CONSTRUCTION
            )

            if Regularity.REGULAR_SPELLING_CHANGE in form_tags:
                tagged_verb.tag(Regularity.REGULAR_SPELLING_CHANGE)

    def analyze_element_phonology(self) -> None:
        _logger.info("analyzing element phonology")
        for tagged_element in self._element_index.values():
            element = tagged_element.value

            tagged_element.tag(*build_phonetic_spelling_tags(element.annotated_form))

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
                del self._lemma_index[tagged_lemma.key]
                for tagged_element in self._element_index.lookup(tagged_lemma.key):
                    del self._element_index[tagged_element.key]

                removed_count += 1
                continue

            tagged_lemma.value.dle_url = dle_lemma.dle_url

        _logger.info("removed %d lemma(s) not found in DLE", removed_count)

    def tag_shared_forms(self) -> None:
        _logger.info("tagging shared forms")

        for tagged_element in self._element_index.values():
            self._spelling_analyzer.tag_shared_forms(tagged_element.key)

    def tag_verb_form_homonym_elements(self) -> None:
        _logger.info("tagging verb form homonym elements")

        homonym_count = 0

        for tagged_form in self._element_index.lookup(PartOfSpeech.VERB):
            for homonym in self._spelling_analyzer.tag_homonyms(tagged_form.key):
                if homonym.part_of_speech is not PartOfSpeech.VERB:
                    self._spelling_analyzer.tag_homonyms(homonym)
                    homonym_count += 1

        _logger.info("tagged %d verb form homonym(s)", homonym_count)

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
            "exported %d lemma(s), %d verb(s)",
            len(export_data.lemmas),
            sum(1 for x in export_data.lemmas if x.part_of_speech is PartOfSpeech.VERB),
        )

        _logger.info(
            "exported %d element(s), %d verb form(s)",
            len(export_data.elements),
            sum(
                1 for x in export_data.elements if x.part_of_speech is PartOfSpeech.VERB
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
