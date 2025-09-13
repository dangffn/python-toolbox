"""File related utils."""

import os
from typing import Iterator

from toolbox.logger import console_err


def iter_files(path: str) -> Iterator[str]:
    if not os.path.exists(path):
        console_err.log(f"Path '{path}' does not exist")
        return
    
    for root, _, files in os.walk(path):
        for file in files:
            yield os.path.join(root, file)