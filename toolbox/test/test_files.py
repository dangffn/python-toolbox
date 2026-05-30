import shutil
from pathlib import Path
import tempfile
import os
import pytest

from toolbox.utils import pipe_bytes, read_bytes, new_path_cleanup


test_data = os.urandom(1_024)


class Ok(Exception):
    pass


@pytest.fixture
def cleanup_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="toolbox-tests"))
    yield temp_dir
    shutil.rmtree(str(temp_dir))
    

@pytest.fixture
def test_files(cleanup_dir):
    _, f1 = tempfile.mkstemp(prefix=f"{cleanup_dir}/test-file")
    _, f2 = tempfile.mkstemp(prefix=f"{cleanup_dir}/test-file")
    with open(f1, "wb") as outfile:
        outfile.write(test_data)
        
    yield f1, f2
    
    
def test_deleted_on_err(cleanup_dir):
    test_file = Path(cleanup_dir) / "one" / "two" / "three" / "four" / "test.txt"
    
    try:
        with new_path_cleanup(test_file) as p:
            assert p.is_file(), "Should be a file"
            raise Ok()
    except Ok:
        pass
        
    assert Path(cleanup_dir).is_dir(), "Should not have removed this parent"
    assert not os.listdir(cleanup_dir), "Not all paths have been cleaned up"
    
    
def test_existing_files_kept(cleanup_dir):
    keep = [
        cleanup_dir / "test.txt",
        cleanup_dir / "one" / "test.txt",
        cleanup_dir / "one" / "two" / "test.txt",
    ]
    
    delete_file = cleanup_dir / "one" / "two" / "three" / "four" / "test.txt"
    
    try:
        with new_path_cleanup(delete_file) as p:
            assert p.is_file(), "Should be a file"
            
            # Create some files before the exception.
            for f in keep:
                f.parent.mkdir(exist_ok=True, parents=True)
                f.touch()
                
            raise Ok()
    except Ok:
        pass
        
    assert cleanup_dir.is_dir(), "Should not have removed this parent"
    for f in keep:
        assert f.exists()
        for p in f.parents:
            assert p.exists()
            
    assert not (cleanup_dir / "one" / "two" / "three").exists(), "This should have been removed"


def test_pipe_bytes(test_files):
    f1, f2 = test_files
    pipe_bytes(f1, f2)
    
    assert read_bytes(f1) == test_data, "Bad read"
    assert read_bytes(f2) == test_data, "Bad write"