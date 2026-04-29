import logging
from typing import TYPE_CHECKING

from joblib import Memory

from conjugation import (
    RegularConstructionConjugator,
    RegularFormConjugator,
    VerbConjugator,
)
from corpes import CORPES
from dle_web import DLEWeb
from resources import obj_path
from tagged_index import TaggedIndex

if TYPE_CHECKING:
    from grammar_model import Element, ElementTag, Lemma, LemmaTag

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

corpes = CORPES()
dle = DLEWeb()
lemma_index: TaggedIndex[LemmaTag, Lemma] = TaggedIndex()
element_index: TaggedIndex[ElementTag, Element] = TaggedIndex()
regular_form_conjugator: VerbConjugator = RegularFormConjugator()
regular_construction_conjugator: VerbConjugator = RegularConstructionConjugator(
    element_index
)

_cache_path = obj_path / "cache"
memory = Memory(location=_cache_path, verbose=0)
