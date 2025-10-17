# pylint: disable=global-statement
"""Test cases for the stego subcommand.
"""

import os
import shutil
from unittest import TestCase
import numpy as np
from PIL import Image

from toolbox.subcommands.stego import Cursor, Container
from toolbox.binary import split, get_mask


class TestCursor(TestCase):
    """Cursor test cases.
    """
    def setUp(self):
        self.cursor = Cursor()
        
    def test_mask(self) -> None:
        self.assertEqual(get_mask(8), 0xFF)
        self.assertEqual(get_mask(3), 0b111)
        
    def test_iter_bits(self) -> None:
        """Split bytes into bit chunks.
        """
        data = np.uint16(0b1010101010101010).tobytes()
        
        # Yield the correct results with default arguments.
        gen = self.cursor.iter_bits(data)
        self.assertListEqual(list(gen), [
            (0b101, 0),
            (0b010, 0),
            (0b101, 0),
            (0b010, 0),
            (0b101, 0),
            (0b0, 3),
        ])
        
        # Yield the correct results with shifted bits.
        gen = self.cursor.iter_bits(data, shift=8)
        self.assertListEqual(list(gen), [
            (0b000, 7),
            (0b000, 7),
            (0b001, 6),
            (0b010, 0),
            (0b101, 0),
            (0b010, 0),
            (0b101, 0),
            (0b010, 0),
        ])
        
    def test_split(self) -> None:
        """Split integers by a bit mask.
        """
        self.assertEqual(split(0xFF, 4), (0xF, 0xF))
        self.assertEqual(split(0xFF, 0), (0xFF, 0x0))
        self.assertEqual(split(0xFF, 8), (0x0, 0xFF))
        self.assertEqual(split(0xFF, -1), (0xFF, 0x0))
        
    def test_seek(self) -> None:
        self.assertEqual(self.cursor.seek(0), (0, 0, 3))
        self.assertEqual(self.cursor.seek(1), (1, 2, 1))
        self.assertEqual(self.cursor.seek(2), (2, 5, 2))


class TestContainer(TestCase):
    def setUp(self) -> None:
        self.container = Container("img.png")
        
    def test_container(self) -> None:
        """Test the image container with the sample image.
        """
        size = self.container.size[0] * self.container.size[1] * 3
        self.assertEqual(len(self.container.data), size)
        
    def test_container_read(self) -> None:
        self.container.write('a' * 4)
        self.container.seek(0)
        # Can read up to the first 4 bytes.
        self.assertEqual(len(self.container.read(0)), 0)
        self.assertEqual(len(self.container.read(4)), 4)
        # No bytes read after that.
        self.assertEqual(len(self.container.read(4)), 0)
    
    def test_container_write(self) -> None:
        self.container.write_from('abcd'.encode(), 0)
        self.assertEqual(self.container.read_from(4, 0), 'abcd'.encode())


class TestImageIntegrity(TestCase):
    def setUp(self) -> None:
        img = Image.new("RGB", (10, 10), 255)
        img.save("temp.png")
        self.container = Container("temp.png")
        
    def tearDown(self) -> None:
        os.remove("temp.png")
        
    def test_initialization(self) -> None:
        val = (255, 0, 0)
        loc = (9, 3)
        pix = Image.open("temp.png").getpixel(loc)
        self.assertEqual(val, pix, "sanity check")
        
        self.container.initialize()
        self.container.save("temp.png")
        
        pix = Image.open("temp.png").getpixel(loc)
        self.assertEqual(val, pix, "value changed after initialization")
        
        self.container.write("abcdefghijklmnop")
        self.container.save("temp.png")
        
        pix = Image.open("temp.png").getpixel(loc)
        self.assertEqual((254, 0, 2), pix, "LSBs incorrectly written!")
