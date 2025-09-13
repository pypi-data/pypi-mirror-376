from __future__ import annotations

import sys
from threading import RLock
from typing import Generic, TypeVar

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self

    SelfNone = Self | None
    """A way to refer to Self | None in Python 3.11 and later"""
else:  # pragma: no cover
    from typing import Union

    from typing_extensions import Self

    SelfNone = Union[Self, None]  # type: ignore[valid-type]
    """A way to refer to Self | None in versions of Python prior to 3.11"""


ATTR_PATTERN = "_{attr}_{cls_name}"

T = TypeVar("T")


class PerClassData(Generic[T]):
    """Holds per-class data for the singleton metaclass."""

    __slots__: tuple = ("instance", "lock")

    def __init__(self) -> None:
        """Initialize the per-class data."""
        self.instance: T | None = None
        self.lock: RLock = RLock()

    def __repr__(self) -> str:
        """Return a string representation of the PerClassData."""
        return f"ClassData(instance={self.instance}, lock={self.lock})"


__all__ = ["ATTR_PATTERN", "Self", "SelfNone"]
