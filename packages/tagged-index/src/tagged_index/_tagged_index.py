from __future__ import annotations

from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass, field
from typing import Generic, TypeVar

_KT = TypeVar("_KT", bound=Hashable)
_VT = TypeVar("_VT")


@dataclass(frozen=True, slots=True)
class _Relationship(Generic[_KT]):
    tag: Hashable
    key: _KT


@dataclass(eq=False)
class TaggedItem(Generic[_KT, _VT]):
    _index: TaggedIndex[_KT, _VT]
    key: _KT
    value: _VT
    tags: set[Hashable] = field(default_factory=set, init=False)

    def tag(self, *tags: Hashable) -> None:
        self.tags.update(tags)
        for tag in tags:
            self._index._lookup[tag].add(self)  # noqa: SLF001

    def relate_to(self, other: TaggedItem[_KT, _VT], tag: Hashable) -> None:
        other.tag(_Relationship(tag, self.key))

    def get_related(self, tag: Hashable) -> set[TaggedItem[_KT, _VT]]:
        return self._index.lookup(_Relationship(tag, self.key))


class TaggedIndex(dict[_KT, TaggedItem[_KT, _VT]], Generic[_KT, _VT]):
    def __init__(self) -> None:
        super().__init__()
        self._lookup: dict[Hashable, set[TaggedItem[_KT, _VT]]] = defaultdict(set)

    def __setitem__(self, key: _KT, item: TaggedItem[_KT, _VT]) -> None:
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

    def __delitem__(self, key: _KT) -> None:
        entry = self[key]
        super().__delitem__(key)
        for tag in entry.tags:
            self._lookup[tag].remove(entry)

    def index(self, key: _KT, value: _VT, /) -> TaggedItem[_KT, _VT]:
        entry = TaggedItem(self, key, value)
        self[key] = entry
        return entry

    def lookup(self, *tags: Hashable) -> set[TaggedItem[_KT, _VT]]:
        if len(tags) == 0:
            return set(self.values())
        sets = [self._lookup[tag] for tag in tags]
        sets.sort(key=len)
        return set.intersection(*sets)
