"""Singleton helper utilities.

Provides a metaclass and base class that make any subclass a singleton.

Usage:
    class MySingleton(metaclass=SingletonMeta):
        pass

    # or
    class MySingleton(Singleton):
        pass

    a = MySingleton()
    b = MySingleton()
    assert a is b
"""

from __future__ import annotations

from threading import Lock
from typing import Dict, Type, TypeVar

T = TypeVar("T")


class SingletonMeta(type):
    """Metaclass that makes subclasses singletons.

    The first time a class using this metaclass is instantiated, the instance
    is created and cached. Subsequent instantiations return the cached
    instance.

    This implementation is thread-safe.
    """

    _instances: Dict[Type, object] = {}
    _lock: Lock = Lock()

    def __call__(cls: Type[T], *args, **kwargs) -> T:  # type: ignore[override]
        """Return the singleton instance for the class, creating it if needed.

        Args:
            *args: Positional arguments forwarded to the class constructor on
                the first instantiation.
            **kwargs: Keyword arguments forwarded to the class constructor on
                the first instantiation.

        Returns:
            The single instance of the class.
        """
        # Use a lock to ensure only one instance is created across threads.
        with SingletonMeta._lock:
            if cls not in SingletonMeta._instances:
                SingletonMeta._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
            return SingletonMeta._instances[cls]  # type: ignore[return-value]


# pylint: disable-next=too-few-public-methods
class Singleton(metaclass=SingletonMeta):
    """Convenience base class to make subclasses singletons.

    Inherit from this class to make the subclass a singleton without having to
    specify the metaclass explicitly.

    Example:
        class Config(Singleton):
            def __init__(self, value: int = 0) -> None:
                self.value = value

        a = Config(3)
        b = Config(4)
        assert a is b
        assert a.value == 3  # constructor ran only the first time
    """

    # No additional implementation required; behavior provided by metaclass.
