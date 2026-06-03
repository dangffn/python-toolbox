# pylint: disable=global-statement
"""Test cases for the stego subcommand.
"""

import pytest
from toolbox.utils import read_bytes
import os
import numpy as np
from PIL import Image

from toolbox.image.stego import Cursor, Container
from toolbox.utils import pipe_bytes, write_bytes, split, get_mask


@pytest.fixture
def container():
    yield Container("img.png")
    
    
@pytest.fixture
def cursor():
    yield Cursor()
    
@pytest.fixture
def image_container():
    img = Image.new("RGB", (10, 10), 255)
    img.save("temp.png")
    yield Container("temp.png")
    os.remove("temp.png")


def test_mask():
    assert get_mask(8) == 0xFF
    assert get_mask(3) == 0b111
        
def test_iter_bits(cursor):
    """Split bytes into bit chunks.
    """
    data = np.uint16(0b1010101010101010).tobytes()
    
    # Yield the correct results with default arguments.
    gen = cursor.iter_bits(data)
    assert list(gen) == [
        (0b101, 0),
        (0b010, 0),
        (0b101, 0),
        (0b010, 0),
        (0b101, 0),
        (0b0, 3),
    ]
    
    # Yield the correct results with shifted bits.
    gen = cursor.iter_bits(data, shift=8)
    assert list(gen) == [
        (0b000, 7),
        (0b000, 7),
        (0b001, 6),
        (0b010, 0),
        (0b101, 0),
        (0b010, 0),
        (0b101, 0),
        (0b010, 0),
    ]
        
def test_split():
    """Split integers by a bit mask.
    """
    assert split(0xFF, 4) == (0xF, 0xF)
    assert split(0xFF, 0) == (0xFF, 0x0)
    assert split(0xFF, 8) == (0x0, 0xFF)
    assert split(0xFF, -1) == (0xFF, 0x0)
    
def test_seek(cursor):
    assert cursor.seek(0) == (0, 0, 3)
    assert cursor.seek(1) == (1, 2, 1)
    assert cursor.seek(2) == (2, 5, 2)


def test_container(container):
    """Test the image container with the sample image.
    """
    size = container.size[0] * container.size[1] * 3
    assert len(container.data) == size
    
def test_container_read(container):
    container.write('a' * 4)
    container.seek(0)
    # Can read up to the first 4 bytes.
    assert len(container.read(0)) == 0
    assert len(container.read(4)) == 4
    # No bytes read after that.
    assert len(container.read(4)) == 0

def test_container_write(container):
    container.write_from('abcd'.encode(), 0)
    assert container.read_from(4, 0) == 'abcd'.encode()
    
def test_container_write_bytes(container):
    container.write("abcdefg".encode("utf-8"))
    container.seek(0)
    assert container.read(3).decode() == "abc"
    container.seek(0)
    assert container.read(0).decode() == ""
    container.seek(0)
    assert container.read(10_000_000).decode() == "abcdefg"
    container.seek(0)
    assert container.read().decode() == "abcdefg"
    
def test_container_pipes(container, test_files):
    f1, f2 = test_files
    write_bytes(os.urandom(256), f1)
    pipe_bytes(f1, container)
    container.seek(0)
    pipe_bytes(container, f2)
    assert read_bytes(f1) == read_bytes(f2)

        
def test_initialization(image_container):
    val = (255, 0, 0)
    loc = (9, 3)
    pix = Image.open("temp.png").getpixel(loc)
    assert val == pix, "sanity check"
    
    image_container.initialize()
    image_container.save("temp.png")
    
    pix = Image.open("temp.png").getpixel(loc)
    assert val == pix, "value changed after initialization"
    
    image_container.write("abcdefghijklmnop")
    image_container.save("temp.png")
    
    pix = Image.open("temp.png").getpixel(loc)
    assert (254, 0, 2) == pix, "LSBs incorrectly written!"
