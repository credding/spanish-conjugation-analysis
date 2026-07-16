# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from .grammar_base_model import BaseElement, BaseLemma


@dataclass
class FreqLemma(BaseLemma):
    freq_adj: float


@dataclass
class FreqElement(BaseElement):
    pass
