from dataclasses import dataclass

from grammar_model import BaseElement, BaseLemma, Element, Lemma


@dataclass
class FreqLemma(BaseLemma):
    freq_adj: float

    def as_lemma(self) -> Lemma:
        return Lemma(self.base_form, self.part_of_speech, freq_adj=self.freq_adj)


@dataclass
class FreqElement(BaseElement):
    def as_element(self, lemma: Lemma) -> Element:
        return Element(self.lemma_tag, self.form, lemma)
