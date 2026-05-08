from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Relationship[KT]:
    tag: Hashable
    key: KT


@dataclass(eq=False)
class TaggedItem[KT: Hashable, VT]:
    _index: TaggedIndex[KT, VT]
    key: KT
    value: VT
    tags: set[Hashable] = field(default_factory=set, init=False)

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

    def relate_to(self, other: TaggedItem[KT, VT], tag: Hashable) -> None:
        other.tag(Relationship(tag, self.key))

    def get_related(self, tag: Hashable) -> set[TaggedItem[KT, VT]]:
        return self._index.lookup(Relationship(tag, self.key))


class TaggedIndex[KT: Hashable, VT](dict[KT, TaggedItem[KT, VT]]):
    def __init__(self) -> None:
        super().__init__()
        self._lookup: dict[Hashable, set[TaggedItem[KT, VT]]] = defaultdict(set)

    def __setitem__(self, key: KT, item: TaggedItem[KT, VT]) -> None:
        if item._index is not self:  # noqa: SLF001
            msg = f"item {item} is not from this index"
            raise ValueError(msg)
        if key in self:
            msg = f"key {key} already exists"
            raise KeyError(msg)
        super().__setitem__(key, item)
        if item.key not in self:
            for tag in item.tags:
                self._lookup[tag].add(item)

    def __delitem__(self, key: KT) -> None:
        entry = self[key]
        super().__delitem__(key)
        for tag in entry.tags:
            self._lookup[tag].remove(entry)

    def index(self, key: KT, value: VT, /) -> TaggedItem[KT, VT]:
        entry = TaggedItem(self, key, value)
        self[key] = entry
        return entry

    def lookup(self, *tags: Hashable) -> ResultSet[TaggedItem[KT, VT]]:
        if len(tags) == 0:
            return ResultSet(self.values())
        return ResultSet(set.intersection(*(self._lookup[tag] for tag in tags)))


class ResultSet[T: TaggedItem](set[T]):
    def difference_tags(self, *tags: Hashable) -> ResultSet[T]:
        return ResultSet(
            self.intersection({x for x in self if x.tags.isdisjoint(tags)})
        )

    def intersection_tags(self, *tags: Hashable) -> ResultSet[T]:
        return ResultSet(
            self.intersection({x for x in self if x.tags.issuperset(tags)})
        )
