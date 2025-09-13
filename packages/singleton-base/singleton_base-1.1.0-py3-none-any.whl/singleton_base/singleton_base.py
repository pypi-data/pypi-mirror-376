"""A base class for singleton classes using a metaclass to enforce the singleton pattern."""

from threading import RLock
from typing import Any, ClassVar

from singleton_base._common import INSTANCE_NAME, Self, SelfNone


class SingletonMeta(type):
    """Metaclass that enforces the singleton pattern."""

    _lock: ClassVar[RLock] = RLock()

    def __call__(cls, *args, **kwargs):
        """Override the __call__ method to control instance creation."""
        class_attr_name: str = INSTANCE_NAME.format(instance_name=cls.__name__)
        if cls._get_instance is None:
            with cls._lock:
                if not cls._get_instance:
                    setattr(cls, class_attr_name, super().__call__(*args, **kwargs))
        return getattr(cls, class_attr_name)

    def _set_instance(cls, value: SelfNone = None) -> None:
        """Set the singleton instance to a new value"""
        setattr(cls, cls.__instance_attr, value)

    @property
    def __instance_attr(cls) -> str:
        """Get the name of the class attribute that holds the singleton instance."""
        return INSTANCE_NAME.format(instance_name=cls.__name__)

    @property
    def _instance(cls) -> Any:
        """Method used when we know the instance is present"""
        return getattr(cls, cls.__instance_attr)

    @property
    def _get_instance(cls) -> SelfNone:
        """Get the singleton instance, or None if it does not exist"""
        return getattr(cls, cls.__instance_attr, None)


class SingletonBase(metaclass=SingletonMeta):
    """A base class for singleton classes"""

    @classmethod
    def get_instance(cls, init: bool = False, **kwargs) -> Self:
        """Return the singleton instance.

        If the instance does not yet exist, it is created using the provided arguments. Uses a lock to ensure thread safety.

        Args:
            init: Whether to initialize the instance if it does not yet exist.
            **kwargs: Arguments passed to ``cls`` when creating the instance.

        Returns:
            Self: The singleton instance of the class.

        Raises:
            RuntimeError: If ``init`` is ``False`` and the instance has not been initialized.
        """
        if not cls.has_instance() and not init:
            raise RuntimeError(f"Instance of {cls.__name__} is not initialized yet")
        if not cls.has_instance() and init:
            with cls._lock:
                if not cls.has_instance():
                    cls._set_instance(cls(**kwargs))
        return cls._instance

    @classmethod
    def has_instance(cls) -> bool:
        """Return ``True`` if the singleton instance has been initialized.

        Returns:
            bool: ``True`` if the instance exists, ``False`` otherwise.
        """
        return cls._get_instance is not None

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance to allow re-initialization.

        Uses a lock to ensure thread safety.
        """
        with cls._lock:
            cls._set_instance()
