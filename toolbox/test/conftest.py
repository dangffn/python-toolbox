import shutil
from pathlib import Path
import tempfile
import pytest


@pytest.fixture
def cleanup_dir():
    temp_dir = Path(tempfile.mkdtemp(prefix="toolbox-tests"))
    yield temp_dir
    shutil.rmtree(str(temp_dir))