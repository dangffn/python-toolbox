import shutil
from pathlib import Path
import pytest
import shlex

from toolbox.utils import list_dir, is_image, sha256_file
from toolbox.main import run


base_dir = Path(__file__).parent


@pytest.fixture
def test_cmd():
    def test_cmd(cmd: str):
        return run(shlex.split(cmd))
    yield test_cmd
    
    
def test_image_scramble_cmd(test_cmd, cleanup_dir):
    # File checksums.
    unscrambled_hash = "a62b9467cc901fe674cf23720ad238d6e00ea49ed1522a36feb739a93be7adc0"
    scrambled_hash = "5ecffdfcdc0f7d1434867a1acf13fc908c1fe5036e287ae8ad26c4be4bd428e1"
    
    shutil.copy(
        str(base_dir / "sample" / "img.png"),
        str(cleanup_dir / "img.png")
    )
    assert sha256_file(cleanup_dir / "img.png") == unscrambled_hash
    
    # Scramble the image.
    assert test_cmd(f"image scramble {cleanup_dir / 'img.png'} --multi") == 0
    assert sha256_file(cleanup_dir / "img.png") == scrambled_hash, "Scramble failed"
    
    # Unscramble the image.
    assert test_cmd(f"image scramble {cleanup_dir / 'img.png'} --multi --unscramble") == 0
    assert sha256_file(cleanup_dir / "img.png") == unscrambled_hash, "Unscramble failed"
    
    
def test_image_scramble_password_cmd(test_cmd, cleanup_dir):
    # File checksums.
    unscrambled_hash = "a62b9467cc901fe674cf23720ad238d6e00ea49ed1522a36feb739a93be7adc0"
    
    shutil.copy(
        str(base_dir / "sample" / "img.png"), 
        str(cleanup_dir / "img.png")
    )
    
    src = cleanup_dir / 'img.png'
    dest_dir = cleanup_dir / 'check'
    dest = dest_dir / 'img.png'
    
    # Record the unscrambled hash and scramble the test file with a password.
    assert test_cmd(f"image scramble {src} --password 12345") == 0
    
    # (Wrong password) unscramble.
    assert test_cmd(f"image scramble {src} --out-dir {dest_dir} --unscramble --password 1234 --multi") == 0
    assert dest.is_file(), 'Unscrambled file was not created'
    assert sha256_file(dest) != unscrambled_hash, 'Unscramble should have failed'
    
    # (Right password) unscramble.
    assert test_cmd(f"image scramble {src} --out-dir {dest_dir} --unscramble --password 12345 --multi") == 0
    assert sha256_file(dest) == unscrambled_hash, 'Unscramble should have succeeded'
        

def test_image_gif_cmd(test_cmd, cleanup_dir):
    input = base_dir / "sample" / "gif.gif"
    output = cleanup_dir / "out_gif"
    
    assert test_cmd(f"image gif extract {input} --out-dir {output}") == 0
    
    assert len(list(filter(is_image, list_dir(output)))) == 4, "Images extracted"