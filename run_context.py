from joblib import Memory

import logging_config
from conjugation import (
    RegularConstructionConjugator,
    RegularFormConjugator,
    VerbConjugator,
)
from corpes import CORPES
from dle_web import DLEWeb
from grammar_model import Element, ElementTag, Lemma, LemmaTag
from resources import obj_path
from tagged_index import TaggedIndex

_ = logging_config

corpes = CORPES()
dle_web = DLEWeb()
lemma_index: TaggedIndex[LemmaTag, Lemma] = TaggedIndex[LemmaTag, Lemma]()
element_index: TaggedIndex[ElementTag, Element] = TaggedIndex[ElementTag, Element]()
regular_form_conjugator: VerbConjugator = RegularFormConjugator()
regular_construction_conjugator: VerbConjugator = RegularConstructionConjugator(
    element_index
)

_cache_path = obj_path / "cache"
memory = Memory(location=_cache_path, verbose=0)
