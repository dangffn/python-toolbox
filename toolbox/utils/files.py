from glob import glob
from PIL import Image
from typing import Literal
import shutil
import io
from pathlib import Path
from contextlib import contextmanager
from hashlib import sha256
from pillow_heif import register_heif_opener
import sys
import os


# Enables opening of .heif images.
register_heif_opener()

Writable = io.RawIOBase | Path | str | Literal["-"]
Readable = Writable | bytes


def pipe_bytes(path_in: Readable, path_out: Writable):
    with bytes_reader(path_in) as infile:
        with bytes_writer(path_out) as outfile:
            shutil.copyfileobj(infile, outfile)


@contextmanager
def bytes_reader(path: Readable):
    if path == "-":
        yield sys.stdin.buffer
    elif isinstance(path, io.RawIOBase):
        yield path
    elif isinstance(path, bytes):
        yield io.BytesIO(path)
    else:
        assert Path(path).is_file(), f"{path} is not a file"
        with Path(path).open("rb") as infile:
            yield infile
            
            
@contextmanager
def bytes_writer(path: Writable):
    if path == "-":
        yield sys.stdout.buffer
    elif isinstance(path, io.RawIOBase):
        yield path
    else:
        if not Path(path).is_file():
            Path(path).parent.mkdir(exist_ok=True, parents=True)
            Path(path).touch()
            
        with Path(path).open("wb") as infile:
            yield infile
            
            
def write_bytes(data: Readable, path: Writable):
    with bytes_reader(data) as infile:
        with bytes_writer(path) as outfile:
            shutil.copyfileobj(infile, outfile)
            

def read_bytes(data: Readable):
    with bytes_reader(data) as infile:
        return infile.read()
    
    
@contextmanager
def new_path_cleanup(path: Path | str, is_file: bool=True):
    """Create the specified files, if an Exception occurs inside the context manager
    The file and parent folders (that were created) will be cleaned up.
    """
    p = Path(path)
    to_delete: list[Path] = list(filter(lambda p: not p.exists(), [p, *p.parents]))
    
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.touch(exist_ok=True) if is_file else p.mkdir(exist_ok=True)
        yield p
    except Exception:
        for delete in to_delete:
            if delete.is_file():
                delete.unlink(missing_ok=True)
            elif delete.is_dir() and not os.listdir(delete):
                delete.rmdir()
        raise
            
            
def walk_dir(path: Path | str):
    p = Path(path)
    assert p.is_dir(), f"{path} is not a directory"
    for root, folers, files in p.walk():
        for f in files:
            yield root / f
            
            
def list_dir(path: Path | str):
    assert Path(path).is_dir(), f"{path} is not a directory"
    for file in glob(f"{path}/*"):
        if Path(file).is_file():
            yield Path(file)
            
            
def multi_file_arg(*path: Path | str, recursive=False):
    """Specify multiple files, or a single directory.
    If a directory is specified, return all files inside.
    """
    files = path
    
    if len(path) > 1:
        files = filter(lambda p: Path(p).is_file(), list(path))
    elif Path(path[0]).is_dir():
        if recursive:
            files = walk_dir(path[0])
        else:
            files = list_dir(path[0])
        
    files = list(map(Path, files))
    assert len(files) > 0, "Specify multiple files or a single directory"
    
    return files


def is_image(path: Path | str):
    try:
        with Image.open(str(path)) as img:
            img.verify()
        return True
    except (SyntaxError, OSError):
        return False
    
    
def sha256_file(path: Readable):
    sha = sha256()
    with bytes_reader(path) as infile:
        while True:
            data = infile.read(65_536)
            if not data:
                break
            sha.update(data)
            
    return sha.hexdigest()
