from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Hashable


@dataclass(frozen=True, slots=True)
class Relationship:
    tag: Hashable
    key: Hashable


@dataclass(eq=False)
class TaggedItem[K: Hashable, V]:
    index: InitVar[TaggedIndex[K, V]]
    key: K
    value: V

    tags: set[Hashable] = field(default_factory=set, init=False)

    def __post_init__(self, index: TaggedIndex[K, V]) -> None:
        self._index = index

    def tag(self, *tags: Hashable) -> None:
        self.tags.update(tags)
        for tag in tags:
            self._index._lookup[tag].add(self)  # noqa: SLF001

    def get_tags[T: Hashable](self, tag_type: type[T]) -> set[T]:
        return {x for x in self.tags if isinstance(x, tag_type)}

    def get_tag_or_none[T: Hashable](self, tag_type: type[T]) -> T | None:
        tags = self.get_tags(tag_type)
        if len(tags) > 1:
            msg = f"multiple tags of type {tag_type} found for item {self.value}"
            raise ValueError(msg)
        return tags.pop() if len(tags) > 0 else None

    def get_tag[T: Hashable](self, tag_type: type[T]) -> T:
        tag = self.get_tag_or_none(tag_type)
        if tag is None:
            msg = f"no tag of type {tag_type} found for item {self.value}"
            raise KeyError(msg)
        return tag

    def relate_to(self, other: TaggedItem[K, V], tag: Hashable) -> None:
        other.tag(Relationship(tag, self.key))

    def get_related(self, tag: Hashable) -> set[TaggedItem[K, V]]:
        return self._index.lookup(Relationship(tag, self.key))


class TaggedIndex[K: Hashable, V]:
    def __init__(self) -> None:
        self._items: dict[K, TaggedItem[K, V]] = {}
        self._lookup: dict[Hashable, set[TaggedItem[K, V]]] = defaultdict(set)

    def __getitem__(self, key: K) -> TaggedItem[K, V]:
        return self._items[key]

    def __contains__(self, key: K) -> bool:
        return key in self._items

    def setdefault(self, key: K, value: V) -> TaggedItem[K, V]:
        entry = self._items.get(key)
        if entry is not None:
            return entry

        entry = TaggedItem(self, key, value)
        self._items[key] = entry
        return entry

    def remove(self, key: K) -> None:
        entry = self._items.pop(key, None)
        if entry is None:
            return
        for tag_set in self._lookup.values():
            tag_set.discard(entry)
        return

    def lookup(self, *tags: Hashable) -> set[TaggedItem[K, V]]:
        if len(tags) == 0:
            return set(self._items.values())
        return set.intersection(*(self._lookup[tag] for tag in tags))
