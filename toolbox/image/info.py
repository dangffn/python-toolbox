
from typing import Tuple
from typing import TypeVar
from typing import Generator
from typing import TypedDict
from typing import Union
from typing import Literal
from rich.table import Table
from toolbox.file import iter_files
import os
from PIL import Image

from toolbox.logger import console
from toolbox.utils import bytes_str


T = TypeVar("T")


Sorters = Literal["height", "width", "name", "size"]


class Info(TypedDict):
    name: str
    height: int
    width: int
    size: int


def get_info(folder_path: str) -> Generator[Info, None, None]:
    for filename in iter_files(folder_path):
        try:
            img = Image.open(filename)
            yield {
                "name":os.path.basename(filename),
                "height": img.height,
                "width": img.width,
                "size": os.path.getsize(filename)
            }
        except Exception:
            pass
        
        
def format(key: Literal["size", "width", "height"], val: int) -> str: ...

def format(key: Literal["name"], val: str) -> str: ...
        
def format(data: Tuple[str, Union[int, str]]):
    key, val = data
    if key == "size":
        return bytes_str(val)
    elif key in ["width", "height"]:
        return f"{val:,}"
    return val


def show_info(folder_path: str, sort: Sorters="size", reverse: bool=False) -> None:
    table = Table("Name", "Height", "Width", "Size")
    
    info = list(get_info(folder_path))
    
    for inf in sorted(info, key=lambda info: info[sort], reverse=reverse):
        table.add_row(*map(format, inf.items()))
    console.print(table)