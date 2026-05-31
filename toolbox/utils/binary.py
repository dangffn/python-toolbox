"""Binary related utils."""

from typing import Tuple


def get_mask(n_bits: int) -> int:
    """Get a mask of N bits.

    Args:
        n_bits (int): number of bits in the mask

    Returns:
        int: integer mask
    """
    return max(1, 2**n_bits) - 1


def split(n: int, shift: int) -> Tuple[int, int]:
    """Split an integer by N bits, returning the most / least significant bits.

    Args:
        n (int): integer to split
        shift (int): bit shift count to split the integer

    Returns:
        Tuple[int, int]: most significant bit integer / least significant bit integer
    """
    shift = min(8, max(0, shift))
    return n >> shift, n & get_mask(shift)
