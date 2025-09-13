import sys

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import Self

    SelfNone = Self | None
    """A way to refer to Self | None in Python 3.11 and later"""
else:  # pragma: no cover
    from typing import Union

    from typing_extensions import Self

    SelfNone = Union[Self, None]  # type: ignore[valid-type]
    """A way to refer to Self | None in versions of Python prior to 3.11"""

INSTANCE_NAME = "_instance_{instance_name}"

__all__ = ["INSTANCE_NAME", "Self", "SelfNone"]
