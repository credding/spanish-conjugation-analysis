from collections import defaultdict
from dataclasses import InitVar, dataclass, field, fields
from typing import Hashable, overload

from grammar_model import Element, Class
from string_analysis import AnnotatedString

type TaggedElement[T: Element] = ElementIndex.TaggedElement[T]


class ElementIndex:
    @dataclass
    class TaggedElement[E: Element]:
        index: InitVar[ElementIndex]
        element: E
        annotated_form: AnnotatedString = field(init=False)
        tags: set[Hashable] = field(default_factory=set)

        @property
        def form(self) -> str:
            return self.element.form

        @property
        def lemma(self) -> str:
            return self.element.lemma

        @property
        def base_form(self) -> str:
            return self.element.base_form

        @property
        def class_(self) -> Class:
            return self.element.class_

        def __post_init__(self, index: ElementIndex):
            self._index = index
            self.annotated_form = AnnotatedString(self.element.form)

        def tag(self, *tags: Hashable):
            self.tags.update(tags)
            for tag in tags:
                self._index._lookup[tag].add(self)

        def get_tags[T](self, cls: type[T]) -> set[T]:
            return {x for x in self.tags if isinstance(x, cls)}

        def get_tag[T](self, cls: type[T]) -> T | None:
            tags = self.get_tags(cls)
            assert len(tags) <= 1
            return tags.pop() if tags else None

        def __eq__(self, other) -> bool:
            return self.element == other.element

        def __hash__(self) -> int:
            return hash(self.element)

    def __init__(self):
        self.all_elements: set[TaggedElement] = set()
        self._lookup: dict[Hashable, set[TaggedElement]] = defaultdict(set)

    def index_element[T: Element](self, element: T) -> TaggedElement[T]:
        tagged_element = self.lookup(element)
        assert len(tagged_element) <= 1
        if tagged_element:
            return tagged_element.pop()

        tagged_element = ElementIndex.TaggedElement(self, element)
        self.all_elements.add(tagged_element)

        tagged_element.tag(element.lemma, element, element.form)
        tagged_element.tag(
            *(
                getattr(element.lemma, x.name)
                for x in fields(element.lemma)
                if x.compare and x.type is not str
            )
        )
        tagged_element.tag(
            *(
                getattr(element, x.name)
                for x in fields(element)
                if x.compare and x.type is not str
            )
        )

        return tagged_element

    @overload
    def lookup[T: Element](
        self, element: T, *tags: Hashable
    ) -> set[TaggedElement[T]]: ...
    @overload
    def lookup[T: Element](
        self, cls: type[T], *tags: Hashable
    ) -> set[TaggedElement[T]]: ...
    @overload
    def lookup(self, *tags: Hashable) -> set[TaggedElement]: ...
    def lookup(self, *tags) -> set[TaggedElement]:
        if not tags:
            return self.all_elements
        if isinstance(tags[0], type):
            return {x for x in self.lookup(*tags[1:]) if isinstance(x.element, tags[0])}
        return set.intersection(*(self._lookup[tag] for tag in tags))
