from rich.table import Table
import os
from PIL import Image
from typing import TypeVar, Generator, TypedDict, Literal, cast

from toolbox.logger import console
from toolbox.utils import bytes_str, walk_dir


T = TypeVar("T")


Sorters = Literal["height", "width", "name", "size"]


class Info(TypedDict):
    name: str
    height: int
    width: int
    size: int


def get_info(folder_path: str) -> Generator[Info, None, None]:
    for file_path in walk_dir(folder_path):
        try:
            img = Image.open(file_path)
            yield {
                "name":os.path.basename(file_path),
                "height": img.height,
                "width": img.width,
                "size": os.path.getsize(file_path)
            }
        except Exception:
            pass
        
        
def format(data: tuple[str, int | str]):
    key, val = data
    if key == "size":
        return bytes_str(cast(int, val))
    elif key in ["width", "height"]:
        return f"{val:,}"
    return val


def show_info(folder_path: str, sort: Sorters="size", reverse: bool=False) -> None:
    table = Table("Name", "Height", "Width", "Size")
    
    info = list(get_info(folder_path))
    
    for inf in sorted(info, key=lambda info: info[sort], reverse=reverse):
        table.add_row(*map(format, inf.items()))
    console.print(table)