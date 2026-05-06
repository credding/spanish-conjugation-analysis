from collections import defaultdict
from collections.abc import Hashable, Iterator, MutableMapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Relationship:
    tag: Hashable
    key: Hashable


@dataclass(eq=False)
class TaggedItem[K: Hashable, V]:
    index: TaggedIndex[K, V]
    key: K
    value: V

    tags: set[Hashable] = field(default_factory=set, init=False)

    def tag(self, *tags: Hashable) -> None:
        tags: set[Hashable] = {tag for tag in tags if tag is not None}
        self.tags.update(tags)
        for tag in tags:
            self.index._lookup[tag].add(self)  # noqa: SLF001

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
        return self.index.lookup(Relationship(tag, self.key))


class TaggedIndex[K: Hashable, V](MutableMapping[K, TaggedItem[K, V]]):
    def __init__(self) -> None:
        self._items: dict[K, TaggedItem[K, V]] = {}
        self._lookup: dict[Hashable, set[TaggedItem[K, V]]] = defaultdict(set)

    def __getitem__(self, key: K) -> TaggedItem[K, V]:
        return self._items[key]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[K]:
        return iter(self._items)

    def __setitem__(self, key: K, value: TaggedItem[K, V], /) -> None:
        if value.index is not self:
            msg = f"value {value} is not from this index"
            raise ValueError(msg)
        self._items[key] = value
        for tag in value.tags:
            self._lookup[tag].add(value)

    def __delitem__(self, key: K) -> None:
        entry = self._items.pop(key, None)
        if entry is None:
            return
        for tag in entry.tags:
            self._lookup[tag].remove(entry)

    def index(self, key: K, value: V) -> TaggedItem[K, V]:
        if key in self._items:
            msg = f"key {key} already exists"
            raise KeyError(msg)
        entry = TaggedItem(self, key, value)
        self._items[key] = entry
        return entry

    def lookup(self, *tags: Hashable) -> set[TaggedItem[K, V]]:
        return set.intersection(*(self._lookup[tag] for tag in tags if tag is not None))
