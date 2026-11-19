#!/usr/bin/env python3

from pathlib import Path
from typing import Protocol, Literal, TypedDict, Unpack
from PIL import Image, ImageOps, ImageChops
import numpy as np

from toolbox.functions.threads import ProgressExecutor
from toolbox.logger import console
from toolbox.subcommands import cli
from toolbox.utils import multi_file_arg, is_image


WHITE = (255, 255, 255)
type Channel = Literal["R", "G", "B", "A"]

class ConverterKwargs(TypedDict, total=False):
    channel: Channel | None
    modifier: float | None
    height: int | None
    width: int | None

class Converter(Protocol):
    def __call__(
        self,
        img: Image.Image,
        **kwargs: Unpack[ConverterKwargs],
    ) -> Image.Image: ...


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def invert(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Invert the image color channel values."""
    r, g, b, a = img.convert("RGBA").split()

    rgb_img = Image.merge("RGB", (r, g, b))
    inverted_rgb = ImageChops.invert(rgb_img)

    inv_r, inv_g, inv_b = inverted_rgb.split()

    return Image.merge("RGBA", (inv_r, inv_g, inv_b, a))


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img"])
def mod_channel(img: Image.Image, /, *, channel: str = None, modifier: float = None):
    """Apply a multiplier modifier to the specified channel.
    
    Args:
        channel (str): One of R, G, B, A
        modifier (float): Normalized float to modify a channel value
    """
    assert channel is not None, "Channel is required"
    assert modifier is not None, "Modifier is required"
    assert 0 <= modifier <= 1, "Modifier must be between 0 and 1"

    rgba_img = img.convert("RGBA")
    data = dict(zip("RGBA", rgba_img.split()))
    data[channel] = data[channel].point(lambda p: min(255, max(0, int(p * modifier))))
    return Image.merge("RGBA", (data["R"], data["G"], data["B"], data["A"]))


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def invert_channel(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Invert a single channel in an image.
    
    Args:
        channel (str): One of R, G, B, A
    """
    channel = kwargs.get("channel")
    assert channel is not None, "Channel is required"

    rgba_img = img.convert("RGBA")
    data = dict(zip("RGBA", rgba_img.split()))
    data[channel] = data[channel].point(lambda p: 255 - p)
    return Image.merge("RGBA", (data["R"], data["G"], data["B"], data["A"]))


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def rgba_white_alpha(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Convert an RGBA to B&W, changing white pixels to transparent."""
    alpha = np.array(img.convert("L"))
    out_array = np.full(alpha.shape + (4,), 255, dtype=np.uint8)
    out_array[:, :, 3] = alpha
    return Image.fromarray(out_array)


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def rgba_white_alpha_bw(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Convert a transparent white sencil to B&W, transparent pixels become black."""
    img = img.convert("RGBA")
    black_bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    final_img = Image.alpha_composite(black_bg, img)
    return final_img.convert("L")


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def resize_and_pad(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Resize the image to the specified dimensions, padding with the specified color."""
    width = kwargs.get("width")
    height = kwargs.get("height")
    assert width, "Must specify a width"
    assert height, "Must specify a height"
    size = (width, height)
    
    with img as img:
        # Convert to RGB to ensure white padding works (handles PNG transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize image while maintaining aspect ratio
        img.thumbnail(size, Image.Resampling.LANCZOS)

        # Create a new white background canvas
        new_img = Image.new("RGB", size, WHITE)

        # Paste the resized image into the center of the canvas
        upper_left = (
            (size[0] - img.size[0]) // 2,
            (size[1] - img.size[1]) // 2
        )
        new_img.paste(img, upper_left)
        return new_img


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def exif_rotate(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """
    Reads an image, rotates it according to EXIF data so it appears upright,
    and saves it back to disk.
    """
    with img as img:
        try:
            fixed_img = ImageOps.exif_transpose(img)
            return fixed_img

        except Exception:
            return img


@cli.register_arg_const("image", "convert", dest="converters", ignores=["img", "kwargs"])
def crop_white(img: Image.Image, **kwargs: Unpack[ConverterKwargs]):
    """Removes white borders from an image."""

    # Tolerance can be increased if the 'white' isn't perfectly #FFFFFF.
    tolerance: int = 0

    # Ensure image is in RGB mode
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Create a solid white background the same size as the image
    bg = Image.new("RGB", img.size, WHITE)

    # Calculate the difference between the image and the white background
    diff = ImageChops.difference(img, bg)

    # If tolerance is needed, apply a threshold here
    if tolerance > 0:
        diff = diff.point(lambda p: p if isinstance(p, float) and p > tolerance else 0)

    # Find the bounding box of the non-white area
    bbox = diff.getbbox()

    if bbox:
        return img.crop(bbox)
    else:
        # If the image is entirely white, return the original or a 1x1 pixel
        return img


def convert_image(
    filename: Path,
    converters: list[Converter],
    overwrite_existing: bool,
    overwrite: bool,
    out_dir: str | None,
    **kwargs: Unpack[ConverterKwargs],
):
    img: Image.Image = Image.open(filename)
    for converter in converters:
        img = converter(img, **kwargs)
    if img:
        *pre, ext = filename.name.split(".")

        if overwrite_existing:
            out_file = filename
        else:
            out_dir_ = Path(out_dir or filename.parent)
            out_dir_.mkdir(parents=True, exist_ok=True)

            out_file = out_dir_ / f"{'.'.join(pre)}_converted.{ext}"

        if overwrite_existing or overwrite or not out_file.exists():
            img.save(out_file)
            return out_file
        
        console.log(f"{out_file} already exists", style="red")
    return None


@cli.register("image", "convert", ignores=["converters", "kwargs"], positional="paths")
def convert_images(paths: list[str], converters: list[Converter], overwrite_existing: bool=False, overwrite: bool=False, recursive: bool=False, out_dir: str | None=None, **kwargs: Unpack[ConverterKwargs]):
    """Convert images with a list of converter methods.
    Args:
        paths (list[str]): Filenames or a folder to run conversions on
        converters (list[Callable]): Conversion functions to run on the images
        overwrite_existing (bool, optional): Overwrite input files, default: false
        overwrite (bool, optional): Overwrite files if they already exist, default: false
        recursive (bool, optional): Recursively search the path if a directory is specified, default: false
    """
    filenames: list[Path] = list(filter(lambda p: is_image(p), multi_file_arg(*paths, recursive=recursive)))
    total = len(filenames)

    with ProgressExecutor[Path | None]() as executor:
        with console.status(f"Converting {total:,} files...") as status:
            for filename in filenames:
                executor.submit(
                    convert_image,
                    filename,
                    converters,
                    overwrite_existing,
                    overwrite,
                    out_dir,
                    **kwargs
                )
                
            for filename in executor.as_completed_progress("Converting images"):
                if filename:
                    status.update(f"Converted [green]{filename}[/]")
