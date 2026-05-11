from collections.abc import Hashable
from dataclasses import dataclass

from annotated_string import AnnotatedString, StringAnnotation
from spanish_grammar import Inflection, Subject, Verb

from ._conjugation_spec import CONJUGATION_SPEC, ConjugationSpecKey


@dataclass(repr=False)
class _AffixAnnotation(StringAnnotation):
    @property
    def unique_key(self) -> Hashable:
        return type(self)


@dataclass(repr=False)
class VerbAffix(_AffixAnnotation):
    pass


@dataclass(repr=False)
class VerbSubject(_AffixAnnotation):
    pass


@dataclass(repr=False)
class VerbVariant(_AffixAnnotation):
    pass


def annotate_verb_form_affix(
    form: AnnotatedString, verb: Verb, inflection: Inflection
) -> None:
    spec = CONJUGATION_SPEC.get(ConjugationSpecKey(verb.ending, inflection))
    if spec is None:
        return

    affix_match = spec.full_affix_pattern.search(form.string)
    if affix_match is None:
        msg = f"expected affix to match {spec.full_affix_pattern.pattern}: {form}"
        raise ValueError(msg)

    form.annotate(VerbAffix, affix_match.start())

    if inflection.subject is not Subject.IMPERSONAL:
        if spec.subject_len is not None:
            subject_start = -spec.subject_len
        else:
            subject_start = affix_match.start()
        form.annotate(VerbSubject, subject_start)

    if inflection.variant is not None:
        form.annotate(VerbVariant, -len(spec.affix))
