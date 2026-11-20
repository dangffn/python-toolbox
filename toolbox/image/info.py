import json as json_
import os
from pathlib import Path
from typing import Literal, TypeVar, TypedDict, cast

from PIL import Image
import imagehash
from rich.table import Table

from toolbox import utils
from toolbox.functions.threads import ProgressExecutor
from toolbox.logger import console
from toolbox.subcommands import cli

T = TypeVar("T")


Sorters = Literal["height", "width", "name", "size"]


class Info(TypedDict):
    """Image basic info object.
    """
    name: str
    height: int
    width: int
    size: int
    dhash: str


def get_dhash(img: Image.Image):
    """Calculate the dhash value of an image."""
    return imagehash.dhash(img)


def get_info(filename: Path | str) -> Info | None:
    """Get basic image info from an image file."""
    try:
        img = Image.open(filename)
        return {
            "name": os.path.basename(filename),
            "height": img.height,
            "width": img.width,
            "size": os.path.getsize(filename),
            "dhash": str(get_dhash(img)),
        }
    except (OSError, ValueError, TypeError) as e:
        console.log(f"Error {e}", style="red")


def fmt_info(data: tuple[str, object]):
    """Format image info tuple as string."""
    key, val = data
    if key == "size":
        return utils.bytes_str(cast(int, val))
    elif key in ["width", "height"]:
        return f"{val:,}"
    return str(val)


@cli.register("image", "info", positional="file_paths")
def show_info(file_paths: list[str], json: bool = False) -> None:
    """Show image info.

    Args:
        file_paths (list[str]): file paths to show info for
        json (bool): print output as json, default: false
    """
    table = Table("Name", "Height", "Width", "Size", "DHash", border_style="#444444")
    output: list[Info] = []

    for filename in filter(utils.is_image, utils.multi_file_arg(*file_paths)):
        info = get_info(filename)
        if info:
            output.append(info)
            table.add_row(*map(fmt_info, info.items()))

    if json:
        print(json_.dumps(output))
    else:
        console.print(table)


@cli.register("image", "find", positional="file_paths")
def find_by_dhash(file_paths: list[str], dhashes: list[str]):
    """Search for visually similar images via dhash values.

    Args:
        file_paths (list[str]): file paths to search in
        dhashes (list[str]): a list of dhash values to compare against the searched images
    """
    matches = set(dhashes)

    def run(filename: Path | str):
        img = Image.open(filename)
        return filename, str(get_dhash(img))

    with ProgressExecutor[tuple[Path | str, str]]() as exc:
        for filename in filter(utils.is_image, utils.multi_file_arg(*file_paths)):
            exc.submit(run, filename)

        for filename, dhash in exc.as_completed_progress(title="Calculating"):
            if dhash in matches:
                console.log(f"[green]{filename}[/] [#444444]({dhash})[/]")
