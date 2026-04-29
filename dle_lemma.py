import logging
import re
from typing import TYPE_CHECKING
from urllib.parse import quote

from dle_model import DLELemma
from grammar_model import LemmaTag, PartOfSpeech
from run_context import dle, memory

if TYPE_CHECKING:
    from dle_web import DLEPage

_logger = logging.getLogger(__name__)


_PART_OF_SPEECH_ABBRS = {
    PartOfSpeech.ADJECTIVE: ["adj."],
    PartOfSpeech.ADVERB: ["adv."],
    PartOfSpeech.AFFIX: ["suf.", "pref."],
    PartOfSpeech.ARTICLE: ["art."],
    PartOfSpeech.CONJUNCTION: ["conj."],
    PartOfSpeech.CONTRACTION: ["contracc."],
    PartOfSpeech.QUANTIFIER: ["adj."],
    PartOfSpeech.DEMONSTRATIVE: ["adj. dem.", "pron. dem."],
    PartOfSpeech.INTERJECTION: ["interj."],
    PartOfSpeech.INTERROGATIVE: ["adj. interrog.", "pron. interrog."],
    PartOfSpeech.NUMERAL: ["m.", "f."],
    PartOfSpeech.POSSESSIVE: ["adj. poses.", "pron. poses."],
    PartOfSpeech.PREPOSITION: ["prep."],
    PartOfSpeech.PERSONAL_PRONOUN: ["pron. person."],
    PartOfSpeech.RELATIVE: ["adj. relat.", "pron. relat."],
    PartOfSpeech.NOUN: ["m.", "f."],
    PartOfSpeech.VERB: ["aux.", "copulat.", "impers.", "intr.", "prnl.", "tr."],
}

_NUMERAL_PATTERN = re.compile(r"^\d+. ")


@memory.cache
def get_lemma(lemma_tag: LemmaTag) -> DLELemma | None:
    _logger.info("fetching lemma data for %s", lemma_tag)

    page = dle.get_page(lemma_tag.base_form)

    dle_url = _get_dle_url(page, lemma_tag)
    if dle_url is None:
        return None

    return DLELemma(page.word, lemma_tag.part_of_speech, dle_url)


def _get_dle_url(page: DLEPage, lemma_tag: LemmaTag) -> str | None:
    article_id = _find_article_id(page, lemma_tag)
    if article_id is None:
        return None

    return f"https://dle.rae.es/{quote(page.word)}#{quote(article_id)}"


def _find_article_id(page: DLEPage, lemma_tag: LemmaTag) -> str | None:
    abbrs = _PART_OF_SPEECH_ABBRS[lemma_tag.part_of_speech]

    for tag in page.document.find_all(class_="c-definitions__item"):
        def_text = _NUMERAL_PATTERN.sub("", tag.get_text())

        for abbr in abbrs:
            if def_text.startswith(abbr):
                article = tag.find_parent("article")
                if article is None:
                    msg = f"missing article for {lemma_tag}"
                    raise ValueError(msg)

                article_id = article["id"]
                if not isinstance(article_id, str):
                    msg = f"invalid article id for {lemma_tag}"
                    raise ValueError(msg)

                return article_id

    return None
