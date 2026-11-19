"""Object helper functions."""

from collections import defaultdict
from typing import TypeVar, Callable, Iterable, Hashable, cast

T = TypeVar("T")


def find(iterable: Iterable[T], func: Callable[[T], bool]) -> T | None:
    """Similar to JavaScripts Array.find, return an item in an array that matches a
    filter function criteria.

    Args:
        array (Iterable[T]): list of items to search
        func (Callable[[T], bool]): lambda returning True for a successful match

    Returns:
        Optional[T]: item that matches the search function criteria
    """
    for item in iterable:
        if func(item):
            return item
    return None


def group_by(items: Iterable[T], func: Callable[[T], Hashable]):
    grouped: dict[Hashable, list[T]] = defaultdict(lambda: [])
    for item in items:
        grouped[func(item)].append(item)
    return grouped


def as_array(val: Iterable[T] | T | None) -> list[T]:
    try:
        if not isinstance(str, val):
            return list(cast(Iterable[T], val))
    except TypeError:
        pass
    return [cast(T, val)]
