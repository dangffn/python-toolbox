import shutil
from pathlib import Path
import tempfile
import pytest


@pytest.fixture
def cleanup_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="toolbox-tests"))
    yield temp_dir
    shutil.rmtree(str(temp_dir))
    

@pytest.fixture
def test_files(cleanup_dir):
    _, f1 = tempfile.mkstemp(prefix=f"{cleanup_dir}/test-file")
    _, f2 = tempfile.mkstemp(prefix=f"{cleanup_dir}/test-file")
    yield f1, f2