# pylint: disable=too-many-instance-attributes
#!/usr/bin/env python3

import argparse
from dataclasses import dataclass
from hashlib import sha256
import sys
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Literal,
    Tuple,
    Union,
    Optional,
)
import os
import time
from random import randbytes
from contextlib import contextmanager
from PIL import Image

from numpy.typing import NDArray
import numpy as np
from rich.table import Table, Column
from rich.progress import track
from rich.emoji import Emoji

from toolbox.logger import console
from toolbox.subcommands.loader import register
from toolbox.utils import bytes_str, find, read_byte_content, write_byte_content
from toolbox.binary import get_mask, split


Pos = Tuple[int, int, int]
Oper = Tuple[Pos, Pos, int, str]
Strategy = Iterator[bytes]


def random_bytes() -> Iterator[bytes]:
    while True:
        yield randbytes(1)
        
def fmt_zeros() -> Iterator[bytes]:
    while True:
        yield np.uint8(0).tobytes()
        
def fmt_ones() -> Iterator[bytes]:
    while True:
        yield np.uint8(0xFF).tobytes()


@dataclass
class Header:
    magic_bytes: bytes = b""
    count: int = 0
    checksum: bytes = b""
    reserved: bytes = b""

    def is_valid(self) -> bool:
        return self.magic_bytes == MAGIC_BYTES


def record_op(kind: Literal["read", "write"]) -> Callable[..., Any]:
    def inner(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(self: "Cursor", *args: Any, **kwargs: Any) -> Any:
            count: int = find(args, lambda a: isinstance(a, (int, str, bytes)))
            if isinstance(count, (str, bytes)):
                count = len(count)
            start = self.seek(None)
            res: Any = func(self, *args, **kwargs)
            end = self.seek(None)
            self.operations.append((start, end, count, kind))
            return res

        return wrapper

    return inner


MAGIC_BYTES = b"=)"


class Cursor:
    """Records byte index and LSB index into a color channel array for incremental IO.

    Data            : [1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0 1 0]
    Index (2)       : [. . .|. . .|1 0 1]
    Bits (1)        : [. . .|. . .|. . 1]
    Position (1):   : [. . . . . . . .|1 0 1 0 1 0 1 0 1]
    """

    def __init__(self, lsb: int=3) -> None:
        # LSB, in this context, is the number of least significant bits to use to write binary data
        # into the individual color channels per image pixel. Larger LSB values allow for more
        # storage capacity, but further degrade the image quality.
        self.lsb = lsb
        self.operations: List[Oper] = []
        self.pos: int = 0
        self.idx: int = 0
        self.lsb_mask = get_mask(lsb)
        self.msb_mask = get_mask(8 - lsb) << lsb

    @classmethod
    def read_header(cls, lsb: int, array: NDArray[np.uint8]) -> Tuple[Header, int]:
        cursor = Cursor(lsb)
        header = Header()
        header.magic_bytes = cursor.read(array, 2)
        header.count = int.from_bytes(cursor.read(array, 4), "big")
        header.checksum = cursor.read(array, 4)
        header.reserved = cursor.read(array, 4)
        return header, cursor.pos

    def write_header(self, header: Header, array: NDArray[np.uint8]) -> None:
        cursor = Cursor(self.lsb)
        cursor.write(array, MAGIC_BYTES[:2])
        cursor.write(array, header.count.to_bytes(4, "big"))
        cursor.write(array, header.checksum)
        cursor.write(array, header.reserved)
        self.operations += cursor.operations

    def _get_bits(self) -> int:
        return self.lsb - ((self.pos * 8) % self.lsb)

    def _seek(self, pos: Union[int, None]) -> Pos:
        if pos is None:
            return self.pos, self.idx, self._get_bits()
        idx = (pos * 8) // self.lsb
        bits = self.lsb - ((pos * 8) % self.lsb)
        return pos, idx, bits

    def seek(self, pos: Union[int, None]) -> Pos:
        pos_ = self._seek(pos)
        self.pos, self.idx, _ = pos_
        return pos_

    def next_byte(self, array: NDArray[np.uint8]) -> int:
        # Read a full byte from the array by concatenating the lsb bits from each array index.
        _, buffer = split(array[self.idx], self._get_bits())
        bits = self._get_bits()
        while bits < 8:
            self.idx += 1
            bits += self.lsb
            buffer = buffer << self.lsb
            buffer |= array[self.idx] & self.lsb_mask

        bits -= 8
        self.pos += 1
        return buffer >> bits

    def get_msb_mask(self, n_bits: int) -> int:
        n_bits = min(self.lsb, max(0, n_bits))
        return get_mask(n_bits) << (self.lsb - n_bits)

    def iter_bits(self, data: bytes, shift: int = 0) -> Iterator[Tuple[int, int]]:
        q = 0
        first_shift = shift

        for byte in data:
            shift += 8
            q = (q << 8) + (byte & 0xFF)

            while shift >= self.lsb:
                shift -= self.lsb
                v, q = split(q, shift)
                yield v, self.get_msb_mask(first_shift)
                first_shift -= self.lsb

        if shift:
            offset = self.lsb - shift
            yield q << offset, get_mask(offset)

    def iter_bytes(self, array: NDArray[np.uint8], count: int) -> Iterator[bytes]:
        bits = self._get_bits()
        # Note: use uint16 here otherwise shifted bits will overflow.
        q = np.uint16(array[self.idx] & get_mask(bits))
        while count > 0:
            self.idx += 1
            bits += self.lsb
            q = q << self.lsb
            q |= array[self.idx] & self.lsb_mask
            if bits >= 8:
                yield np.uint8(q >> (bits - 8)).tobytes()
                count -= 1
                self.pos += 1
                bits -= 8
        self.seek(self.pos)

    @record_op("read")
    def read(self, array: NDArray[np.uint8], count: int) -> bytes:
        return b"".join(self.iter_bytes(array, count))

    @record_op("write")
    def write(self, array: NDArray[np.uint8], data: bytes) -> None:
        shift = self.lsb - self._get_bits()

        arr = np.array(list(self.iter_bits(data, shift=shift)), dtype=np.uint8)
        if len(arr) <= 0:
            return
        
        bit_mask = np.uint8(0xFF & self.msb_mask)
        arr[:, 1] |= bit_mask
        
        # Mask the existing bits.
        array[self.idx : self.idx + len(arr)] &= bit_mask #arr[:, 1]
        # Write in the new LSB bits.
        array[self.idx : self.idx + len(arr)] |= arr[:, 0]
        
        self.seek(self.pos + len(data))

    def __str__(self) -> str:
        return f"<Cursor: lsb={self.lsb} idx={self.idx} pos={self.pos} bits={self._get_bits()} />"


class Container:
    def __init__(self, filename: str, lsb: int = 2) -> None:
        self.filename = os.path.abspath(filename)
        self.lsb = lsb
        self.img = Image.open(filename)
        self.size = self.img.size
        assert self.img.mode == "RGB", f"Unsupported image mode {self.img.mode}"
        self.data = np.asarray(self.img, dtype=np.uint8).flatten()
        self.header, self.header_end = Cursor.read_header(self.lsb, self.data)
        self.cursor: Cursor = Cursor(lsb)
        self.cursor.seek(self.header_end)

    @contextmanager
    @staticmethod
    def open(
        filename: str, initialize: bool = False, force: bool = False
    ) -> Iterator["Container"]:
        try:
            container = Container(filename)
        except (FileNotFoundError, PermissionError) as e:
            console.log(f"Failed to open {filename} ({e})")
            sys.exit(1)
            
        if initialize:
            container.initialize(force)
        yield container
        write_op = find(container.cursor.operations, lambda o: o[3] == "write")
        if write_op or initialize:
            container.save()

    def get_capacity(self) -> int:
        # Return the capacity in bytes this image can hold.
        return ((len(self.data) * self.lsb) // 8) - self.header_end

    def _validate(self, header_only: bool = False) -> None:
        assert self.header.is_valid(), f"{self.filename} has an invalid header"
        if header_only:
            return

        # Calculate the checksum digest.
        checksum = self.calc_checksum()
        assert (
            checksum == self.header.checksum
        ), f"{self.filename} has an invalid checksum {checksum.hex()} != {self.header.checksum.hex()}"

    def validate(self, header_only: bool = False) -> None:
        try:
            self._validate(header_only)
            console.log(
                f"[green]:heavy_check_mark: Valid[/green] {self.filename} is a valid container"
            )
        except AssertionError as e:
            console.log(f"[red]:x: Invalid[/red] {e}")

    def read_from(self, count: int, pos: int) -> bytes:
        curr_pos = self.cursor.pos
        self.seek(pos)
        res = self.read(count)
        self.seek(curr_pos)
        return res

    def read(self, count: Optional[int] = None) -> bytes:
        assert self.header.is_valid(), "Attempt to read from an invalid container"
        max_pos = self.header.count + self.header_end
        max_count = max_pos - self.cursor.pos
        if count is not None:
            if max_count < count:
                console.log(f"Read past boundary ([red]{count:,}[/red] > {max_count:,})")
                count = max_count
        else:
            count = max_count
        return self.cursor.read(self.data, count)

    def write_from(self, data: Union[str, bytes], pos: int) -> None:
        curr_pos = self.cursor.pos
        self.seek(pos)
        self.write(data)
        self.seek(curr_pos)

    def write(self, data: Union[str, bytes]) -> None:
        assert self.header.is_valid(), "Attempt to write to an invalid container"
        with console.status("Writing data to pixel channel LSBs..."):
            if type(data) == str:
                data = data.encode()
            self.cursor.write(self.data, data)
            self.header.count = len(data)

    def calc_checksum(self) -> bytes:
        chk = sha256(self.read_from(self.header.count, 0)).digest()[:4]
        return chk

    def save(self, filename: Optional[str] = None) -> None:
        self.filename, _ = os.path.splitext(os.path.abspath(filename or self.filename))
        self.filename = f"{self.filename}.png"
        
        with console.status(f"Saving [green]{self.filename}[/green]...") as status:
            self.header.checksum = self.calc_checksum()
            status.update("Writing header...")
            self.cursor.write_header(self.header, self.data)
            
            status.update("Writing output image...")
            shape = (self.size[1], self.size[0], 3)
            img = Image.fromarray(self.data.reshape(shape))
            img.save(self.filename)

    def seek(self, pos: Union[int, None]) -> Pos:
        # Constrain the container seek position to the header boundary.
        pos = pos + self.header_end if pos is not None else None
        return self.cursor.seek(pos)

    def _initialize(self, force: bool = False) -> None:
        assert (
            force or not self.header.is_valid()
        ), f"{self.filename} is already a container, refusing to initialize"

        self.header = Header(
            magic_bytes=MAGIC_BYTES,
            count=0,
            checksum=sha256(b"").digest()[4:],
            reserved=(0).to_bytes(4, "big"),
        )

    def initialize(self, force: bool = False) -> None:
        try:
            self._initialize(force)
            console.log(
                f"[green]:heavy_check_mark: Initialized[/green] {self.filename} can now be used as a data container"
            )
        except AssertionError as e:
            console.log(f"[red]:x: Failed[/red] {e}")
            
    def format(self, strategy: Strategy) -> None:
        self.seek(0)
        strat = getattr(strategy, "__name__", "unknown")
        console.log(f"Formatting with strategy: [red]{strat}[/red]")
        # TODO: optimize me
        # Note, this can be severely optimized, per-byte container writing is slow, the values can
        # instead be written directly into the color channel array with numpy.
        # I haven't gotten around to it yet, and the loading bar is neat ¯\_(ツ)_/¯.
        for _ in track(range(self.get_capacity()), description="Formatting..."):
            self.cursor.write(self.data, next(strategy))
        self.header.count = 0
            
            
def cat(file_path: str, out_file: str) -> None:
    with Container.open(file_path) as c:
        write_byte_content(out_file, c.read())
        
        
def write(file_path: str, data: str) -> None:
    with Container.open(file_path) as c:
        c.write(read_byte_content(data))
        
        
def initialize(file_path: str, force: bool) -> None:
    with Container.open(file_path, initialize=True, force=force):
        pass
    

def validate(file_path: str, header_only: bool) -> None:
    with Container.open(file_path) as c:
        c.validate(header_only)
        
        
def format(file_path: str, strategy: Strategy) -> None:
    with Container.open(file_path) as c:
        c.format(strategy)
        

def info(file_path: str) -> None:
    with Container.open(file_path) as c:
        table = Table(
            Column("Info", style="white"),
            Column("Data", style="cyan", width=50),
            border_style="#444444",
            title=file_path,
        )
        is_valid = c.header.is_valid()
        style_valid = "white" if is_valid else "red"
        
        validity_str = Emoji("heavy_check_mark", style="green") \
            if is_valid else \
            Emoji("x", style="red")
            
        max_color_integrity = len(c.data) * 256
        current_pos = c.cursor._seek(c.header.count)[1]
        degredation = (get_mask(c.lsb) + 1) * current_pos
        current_color_integrity = ((max_color_integrity - degredation) / max_color_integrity) * 100
        integrity_color = "green" if current_color_integrity > 99 else "red"
            
        table.add_row("Header", validity_str)
        table.add_row("Dimensions", f"{c.size[1]:,} px X {c.size[0]:,} px")
        table.add_row("Capacity", bytes_str(c.get_capacity()))
        usage = f"{c.header.count / c.get_capacity() * 100:.0f}%"
        table.add_row("Used", f"{bytes_str(c.header.count)} ({usage})", style=style_valid)
        table.add_row("Channel LSBs", f"{len(c.data):,} x {c.lsb}", style=style_valid)
        table.add_row("Checksum", c.header.checksum.hex(), style=style_valid)
        table.add_row("Reserved bits", c.header.reserved.hex().rjust(8, "0"), style=style_valid)
        table.add_row("Header end", f"{c.header_end if is_valid else 'n/a'}", style=style_valid)
        table.add_row("Visual integrity", f"{current_color_integrity:.2f}%", style=integrity_color)
        
        console.print(table)


@register("stego", description="Image based steganography tools")
def setup_parser(parser: argparse.ArgumentParser) -> None:

    subparsers = parser.add_subparsers()

    initialize_parser = subparsers.add_parser(
        "initialize", help="Initialize a new image container"
    )
    initialize_parser.add_argument("file_path", help="Image file to convert to a container")
    initialize_parser.add_argument("-f", "--force", action="store_true", help="Force re-initialize existing containers")
    initialize_parser.set_defaults(func=initialize)
    
    validate_parser = subparsers.add_parser("validate", help="Validate the contents of a container")
    validate_parser.add_argument("file_path", help="Image file to validate")
    validate_parser.add_argument("--header-only", action="store_true", help="Only validate the contents of the header")
    validate_parser.set_defaults(func=validate)
    
    cat_parser = subparsers.add_parser("cat", help="Dump the contents of an image container")
    cat_parser.add_argument("file_path", help="Image file container to read")
    cat_parser.add_argument("-o", "--out-file", default="-", help="Output file to write contents to, default stdout")
    cat_parser.set_defaults(func=cat)
    
    write_parser = subparsers.add_parser("write", help="Write data into an existing container")
    write_parser.add_argument("file_path", help="Image file container to write to")
    write_parser.add_argument("--data", default="-", help="Data to write into the container, default reads from stdin")
    write_parser.set_defaults(func=write)
    
    format_parser = subparsers.add_parser("format", help="Format the pixel channel LSBs, deleting all written data")
    format_parser.add_argument("file_path", help="Image file container to format")
    format_group = format_parser.add_mutually_exclusive_group()
    format_group.add_argument("--random", action="store_const", const=random_bytes(), dest="strategy", help="Format the data with random bytes")
    format_group.add_argument("--zeros", action="store_const", const=fmt_zeros(), dest="strategy", help="Format the data with all 0s")
    format_group.add_argument("--ones", action="store_const", const=fmt_ones(), dest="strategy", help="Format the data with all 1s")
    format_parser.set_defaults(func=format, strategy=random_bytes())
    
    info_parser = subparsers.add_parser("info", help="Show container information")
    info_parser.add_argument("file_path", help="Image file container to inspect")
    info_parser.set_defaults(func=info)
    