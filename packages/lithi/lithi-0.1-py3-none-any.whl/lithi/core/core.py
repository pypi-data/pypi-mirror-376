"""
Core utilities
"""

from functools import wraps
from typing import Any, Dict, Type, TypeVar, cast

_T = TypeVar("_T")

# Global instances dictionary
_instances: Dict[Type[Any], Any] = {}


def singleton(cls: Type[_T]) -> Type[_T]:
    """
    Pythonic singleton decorator, subclass-safe.
    Access instance via .get().
    """
    original_init = cls.__init__

    @wraps(original_init)
    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        if cls in _instances:
            raise RuntimeError(
                f"{cls.__name__} is a singleton. Use {cls.__name__}.get()"
            )
        original_init(self, *args, **kwargs)

    def get(cls: Type[_T], *args: Any, **kwargs: Any) -> _T:
        if cls not in _instances:
            # Temporarily restore original __init__ to avoid RuntimeError
            cls.__init__ = original_init  # type: ignore[method-assign]
            try:
                _instances[cls] = cls(*args, **kwargs)
            finally:
                # Restore the singleton __init__
                cls.__init__ = __init__  # type: ignore[method-assign]
        return cast(_T, _instances[cls])

    # Replace the __init__ method
    cls.__init__ = __init__  # type: ignore[method-assign]

    # Add the get class method
    setattr(cls, "get", classmethod(get))

    return cls
