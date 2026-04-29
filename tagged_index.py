from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Relationship:
    tag: Any
    key: Any


@dataclass(eq=False)
class TaggedItem[K, V]:
    index: InitVar[TaggedIndex]
    key: K
    value: V

    tags: set[Any] = field(default_factory=set, init=False)

    def __post_init__(self, index: TaggedIndex[Any, Any]):
        self._index = index

    def tag(self, *tags: Any):
        self.tags.update(tags)
        for tag in tags:
            self._index._lookup[tag].add(self)

    def get_tags[T: Any](self, tag_type: type[T]) -> set[T]:
        return {x for x in self.tags if isinstance(x, tag_type)}

    def get_tag_or_none[T: Any](self, tag_type: type[T]) -> T | None:
        tags = self.get_tags(tag_type)
        if len(tags) > 1:
            raise ValueError(
                f"multiple tags of type {tag_type} found for item {self.value}"
            )
        return tags.pop() if len(tags) > 0 else None

    def get_tag[T: Any](self, tag_type: type[T]) -> T:
        tag = self.get_tag_or_none(tag_type)
        if tag is None:
            raise KeyError(f"no tag of type {tag_type} found for item {self.value}")
        return tag

    def relate_to(self, other: TaggedItem[K, V], tag: Any):
        other.tag(Relationship(tag, self.key))

    def get_related(self, tag: Any) -> set[TaggedItem[K, V]]:
        return self._index.lookup(Relationship(tag, self.key))


class TaggedIndex[K, V]:
    def __init__(self):
        self._items: dict[K, TaggedItem[K, V]] = dict()
        self._lookup: dict[Any, set[TaggedItem[K, V]]] = defaultdict(set)

    def __getitem__(self, key: K) -> TaggedItem[K, V]:
        return self._items[key]

    def setdefault(self, key: K, value: V) -> TaggedItem[K, V]:
        entry = self._items.get(key)
        if entry is not None:
            return entry

        entry = TaggedItem(self, key, value)
        self._items[key] = entry
        return entry

    def lookup(self, *tags: Any) -> set[TaggedItem[K, V]]:
        if len(tags) == 0:
            return set(self._items.values())
        return set.intersection(*(self._lookup[tag] for tag in tags))
