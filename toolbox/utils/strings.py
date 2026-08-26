"""Utility functions to make life easier.
"""

from typing import TypeVar, Callable, Iterable


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


def bytes_str(num: float | int) -> str:
    """Friendly number string. Ie: 12340 -> 12.34k

    :param int num: number to format
    :return str: formatted string
    """
    suffix = ["bytes", "KB", "MB", "GB", "TB", "PB"]
    idx = 0
    while num > 1_024 and idx < len(suffix):
        num /= 1_024
        idx += 1
    if idx == 0:
        num = int(num)
        return f"{num:,} {suffix[idx]}"
    return f"{num:,.2f} {suffix[idx]}"


def time_delta_string(num: int | float) -> str:
    """Friendly time delta string. Ie: 12min 34sec

    :param int | float num: time delta in seconds
    :return str: formatted string
    """
    times = {
        3600 * 24 * 365: "year",
        3600 * 24 * 7: "week",
        3600 * 24: "day",
        3600: "hour",
        60: "minute",
        1: "sec",
    }
    string: list[str] = []
    for val, key in times.items():
        incr = int(num / val)
        if incr > 0:
            string.append(f"{incr:,} {key}{'s' if incr > 1 and key != 'sec' else ''}")
            num -= incr * val
    return f"{' '.join(string)}"


def as_array(val: list[str] | str | None):
    if val is None:
        return []
    return [val] if isinstance(val, str) else val
