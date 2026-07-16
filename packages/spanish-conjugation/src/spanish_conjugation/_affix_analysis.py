# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from annotated_string import AnnotatedString, SingletonStringAnnotation
from spanish_grammar import Inflection, Subject, Verb

from ._conjugation_spec import CONJUGATION_SPEC, ConjugationSpecKey


@dataclass(repr=False)
class VerbAffix(SingletonStringAnnotation):
    pass


@dataclass(repr=False)
class VerbSubject(SingletonStringAnnotation):
    pass


@dataclass(repr=False)
class VerbVariant(SingletonStringAnnotation):
    pass


def annotate_verb_form_affix(
    form: AnnotatedString, verb: Verb, inflection: Inflection
) -> None:
    spec = CONJUGATION_SPEC[ConjugationSpecKey(verb.ending, inflection)]

    affix_match = spec.full_affix_pattern.search(form.string)
    if affix_match is None:
        msg = f"expected affix to match {spec.full_affix_pattern.pattern}: {form}"
        raise ValueError(msg)

    affix = VerbAffix(form.string, affix_match.start(), len(form.string))
    form.add_annotation(affix)

    if inflection.subject is not Subject.IMPERSONAL:
        if spec.subject_len is not None:
            subject_start = len(form.string) - spec.subject_len
        else:
            subject_start = affix_match.start()
        subject = VerbSubject(form.string, subject_start, len(form.string))
        form.add_annotation(subject)

    if inflection.variant is not None:
        variant_start = len(form.string) - len(spec.affix)
        variant = VerbVariant(form.string, variant_start, variant_start + 2)
        form.add_annotation(variant)
