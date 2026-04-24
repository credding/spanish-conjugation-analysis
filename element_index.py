from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import Any, Literal, overload

from grammar_model import Class, Element, Form, Lemma, VerbForm
from string_analysis import AnnotatedString

type TaggedElement[T: Element] = ElementIndex.TaggedElement[T]


class ElementIndex:
    @dataclass(eq=False)
    class TaggedElement[E: Element]:
        index: InitVar[ElementIndex]

        element: E

        lemma: Lemma = field(init=False)
        class_: Class = field(init=False)
        form: Form = field(init=False)

        annotated_form: AnnotatedString = field(init=False)
        tags: set[Any] = field(init=False)

        _relationships: dict[Any, set[TaggedElement]] = field(
            init=False, default_factory=lambda: defaultdict(set)
        )

        def __post_init__(self, index: ElementIndex):
            self._index = index

            self.lemma = self.element.lemma
            self.class_ = self.element.lemma.class_
            self.form = Form(self.element.form)

            self.annotated_form = AnnotatedString(self.element.form)
            self.tags = set()

            self.tag(self.element, self.form, self.lemma, self.class_)
            if isinstance(self.element, VerbForm):
                self.tag(self.element.tense, *self.element.subject_group)
                if self.element.variant is not None:
                    self.tag(self.element.variant)

        def tag(self, *tags: Any):
            self.tags.update(tags)
            for tag in tags:
                self._index._lookup[tag].add(self)

        def get_tags[T](self, cls: type[T]) -> set[T]:
            return {x for x in self.tags if isinstance(x, cls)}

        @overload
        def get_tag[T](
            self, cls: type[T], /, raise_if_absent: Literal[True] = True
        ) -> T: ...
        @overload
        def get_tag[T](
            self, cls: type[T], /, raise_if_absent: bool = True
        ) -> T | None: ...
        def get_tag[T](self, cls: type[T], /, raise_if_absent: bool = True) -> T | None:
            tags = self.get_tags(cls)
            if len(tags) == 0:
                if raise_if_absent:
                    raise KeyError(
                        f"no tag of type {cls} found for element {self.element}"
                    )
                return None
            if len(tags) > 1:
                raise ValueError(
                    f"multiple tags of type {cls} found for element {self.element}"
                )
            return tags.pop()

        def relate_to(self, other: TaggedElement, *tags: Any):
            for tag in tags:
                self._relationships[tag].add(other)

        def get_related(self, tag: Any) -> set[TaggedElement]:
            return self._relationships[tag]

    def __init__(self):
        self.all_elements: set[TaggedElement] = set()
        self._lookup: dict[Any, set[TaggedElement]] = defaultdict(set)

    def index_element[T: Element](self, element: T) -> TaggedElement[T]:
        tagged_element = self.lookup(element)
        if len(tagged_element) > 0:
            assert len(tagged_element) == 1
            return tagged_element.pop()

        tagged_element = ElementIndex.TaggedElement(self, element)
        self.all_elements.add(tagged_element)
        return tagged_element

    @overload
    def lookup[T: Element](self, tag: T, *tags: Any) -> set[TaggedElement[T]]: ...
    @overload
    def lookup[T: Element](
        self, cls: type[T], tag: Any, *tags: Any
    ) -> set[TaggedElement[T]]: ...
    @overload
    def lookup(self, tag: Any, *tags: Any) -> set[TaggedElement]: ...
    def lookup(self, cls, *tags) -> set[TaggedElement]:
        if not isinstance(cls, type):
            cls, tags = None, (cls,) + tags
        result = set.intersection(*(self._lookup[tag] for tag in tags))
        if cls is None:
            return result
        return {x for x in result if isinstance(x.element, cls)}
