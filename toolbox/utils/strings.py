"""String helper functions."""

from typing import TypeVar
from datetime import timedelta

T = TypeVar("T")



def pluralize(n: float, form: str | tuple[str, str]):
    if isinstance(form, tuple):
        singular, plural = form
    else:
        singular = form
        plural = singular + "s"
    return f"{number_str(n)} {singular if abs(n) == 1 else plural}"


def number_str(n: float | int):
    if int(n) == n:
        n = int(n)
    return f"{n:,.2f}" if isinstance(n, float) else f"{n:,}"


def bytes_str(num: float | int) -> str:
    """Friendly number string. Ie: 12340 -> 12.34k

    :param int num: number to format
    :return str: formatted string
    """
    suffix = ["byte", ("KB", "KB"), ("MB", "MB"), ("GB", "GB"), ("TB", "TB"), ("PB", "PB")]
    idx = 0
    while abs(num) >= 1_024 and idx < len(suffix):
        num /= 1_024
        idx += 1
    if idx == 0:
        num = int(num)
    return pluralize(num, suffix[idx])


def timedelta_str(num: timedelta | int | float) -> str:
    """Friendly time delta string. Ie: 12min 34sec

    :param int | float num: time delta in seconds
    :return str: formatted string
    """
    if isinstance(num, timedelta):
        num = num.total_seconds()
        
    times = {
        3600 * 24 * 365: "year",
        3600 * 24 * 7: "week",
        3600 * 24: "day",
        3600: "hour",
        60: "minute",
        1: "second",
        0.001: ("ms", "ms"),
        0.000001: ("μs", "μs"),
        0.000000001: ("ns", "ns"),
        0.000000000001: ("ps", "ps"),
    }
    string: list[str] = []
    for val, key in times.items():
        incr = int(num / val)
        if abs(incr) > 0:
            string.append(pluralize(incr, key))
            num -= incr * val
    return f"{' '.join(string)}" if string else "0 seconds"
