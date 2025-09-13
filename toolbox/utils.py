"""Utility functions to make life easier.
"""

from typing import TypeVar, Union, List, Tuple, Callable, Optional
import sys
import os


T = TypeVar("T")


def find(array: Union[List[T], Tuple[T]], func: Callable[[T], bool]) -> Optional[T]:
    """Similar to JavaScripts Array.find, return an item in an array that matches a 
    filter function criteria.

    Args:
        array (Union[List[T], Tuple[T]]): list of items to search
        func (Callable[[T], bool]): lambda returning True for a successful match

    Returns:
        Optional[T]: item that matches the search function criteria
    """
    for item in array:
        if func(item):
            return item
    return None


def read_byte_content(file_or_data: str) -> bytes:
    if file_or_data == "-":
        return sys.stdin.buffer.read()
    if os.path.isfile(file_or_data):
        with open(file_or_data, "rb") as infile:
            return infile.read()
    return file_or_data.encode()


def write_byte_content(file: str, data: bytes) -> None:
    if os.path.isfile(file):
        with open(file, "wb") as outfile:
            outfile.write(data)
    elif file == "-":
        sys.stdout.buffer.write(data)
    else:
        raise ValueError(f"Could not determine output file destination [{file}]")


def bytes_str(num: float) -> str:
    """Friendly number string. Ie: 12340 -> 12.34k

    :param int num: number to format
    :return str: formatted string
    """
    suffix = ["bytes", "kb", "mb", "gb", "tb", "pb"]
    idx = 0
    while num > 1_024 and idx < len(suffix):
        num /= 1_024
        idx += 1
    if idx == 0:
        num = int(num)
        return f"{num:,} {suffix[idx]}"
    return f"{num:,.2f} {suffix[idx]}"


def time_delta_string(num: int) -> str:
    """Friendly time delta string. Ie: 12min 34sec

    :param int num: time delta in seconds
    :return str: formatted string
    """
    times = {
        3600 * 24 * 365: "year",
        3600 * 24 * 7: "week",
        3600 * 24: "day",
        3600: "hour",
        60: "minute",
        1: "sec"
    }
    string: List[str] = []
    for val, key in times.items():
        incr = int(num / val)
        if incr > 0:
            string.append(f"{incr:,} {key}{'s' if incr > 1 and key != 'sec' else ''}")
            num -= (incr * val)
    return f"{' '.join(string)}"
