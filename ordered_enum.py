from enum import Enum
from typing import Self


class OrderedEnum(Enum):
    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        members = [*type(self)]
        return members.index(self) < members.index(other)
