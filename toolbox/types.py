import functools
from typing import ParamSpec, TypeVar, Callable


P = ParamSpec("P")
R = TypeVar("R")


def with_signature(source: Callable[P, R]) -> Callable[[Callable], Callable[P, R]]:
    """Decorator to copy the type signature from one function to another.
    """
    @functools.wraps(source)
    def decorator(target: Callable) -> Callable[P, R]:
        return functools.update_wrapper(target, source)
    return decorator
