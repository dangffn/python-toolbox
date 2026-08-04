from pathlib import Path
import os


from toolbox.utils import pipe_bytes, read_bytes, new_path_cleanup


class Ok(Exception):
    pass
    
    
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
    
    test_data = os.urandom(1_024)
    pipe_bytes(test_data, f1)
    
    pipe_bytes(f1, f2)
    
    assert read_bytes(f1) == test_data, "Bad read"
    assert read_bytes(f2) == test_data, "Bad write"