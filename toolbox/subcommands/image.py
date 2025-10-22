import argparse
import os
from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual_imageview.viewer import ImageViewer
from PIL import Image

from toolbox.subcommands.loader import register
from toolbox.image.gif import extract_images_from_gif, write_gif_from_frames
from toolbox.image.stego import initialize, validate, cat, write, fmt_ones, fmt_zeros, random_bytes, info
from toolbox.image.scramble import main as scramble_main


@register("image", description="Image related utilities")
def setup_image(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(func=parser.print_help)


@register("image", "gif", description="Create and extract GIF images")
def setup_image_gif(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers()
    
    # Gif -> images.
    parser_extract = subparsers.add_parser("extract", help="Extract images from a Gif")
    parser_extract.add_argument("gif_file", help="Path to the .gif file")
    parser_extract.add_argument("--out-folder", default="out", help="Folder to save extracted frames to")
    parser_extract.set_defaults(func=extract_images_from_gif)
    
    # Images -> Gif.
    parser_build = subparsers.add_parser("build", help="Build a .gif from image frames")
    parser_build.add_argument("image_folder", help="Directory containing images to combine into a .gif")
    parser_build.add_argument("--out-file", default="./build.gif", help="Filename of the .gif to create")
    parser_build.add_argument("--duration", type=int, default=80, help="The amount of time (ms) for each frame")
    parser_build.set_defaults(func=write_gif_from_frames)

@register("image", "stego", description="Image based steganography tools")
def setup_image_stego(parser: argparse.ArgumentParser) -> None:

    subparsers = parser.add_subparsers()

    initialize_parser = subparsers.add_parser(
        "initialize", help="Initialize a new image container"
    )
    initialize_parser.add_argument("file_path", help="Image file to convert to a container")
    initialize_parser.add_argument("-f", "--force", action="store_true", help="Force re-initialize existing containers")
    initialize_parser.set_defaults(func=initialize)
    
    validate_parser = subparsers.add_parser("validate", help="Validate the contents of a container")
    validate_parser.add_argument("file_path", help="Image file to validate")
    validate_parser.add_argument("--header-only", action="store_true", help="Only validate the contents of the header")
    validate_parser.set_defaults(func=validate)
    
    cat_parser = subparsers.add_parser("cat", help="Dump the contents of an image container")
    cat_parser.add_argument("file_path", help="Image file container to read")
    cat_parser.add_argument("-o", "--out-file", default="-", help="Output file to write contents to, default stdout")
    cat_parser.set_defaults(func=cat)
    
    write_parser = subparsers.add_parser("write", help="Write data into an existing container")
    write_parser.add_argument("file_path", help="Image file container to write to")
    write_parser.add_argument("--data", default="-", help="Data to write into the container, default reads from stdin")
    write_parser.set_defaults(func=write)
    
    format_parser = subparsers.add_parser("format", help="Format the pixel channel LSBs, deleting all written data")
    format_parser.add_argument("file_path", help="Image file container to format")
    format_group = format_parser.add_mutually_exclusive_group()
    format_group.add_argument("--random", action="store_const", const=random_bytes(), dest="strategy", help="Format the data with random bytes")
    format_group.add_argument("--zeros", action="store_const", const=fmt_zeros(), dest="strategy", help="Format the data with all 0s")
    format_group.add_argument("--ones", action="store_const", const=fmt_ones(), dest="strategy", help="Format the data with all 1s")
    format_parser.set_defaults(func=format, strategy=random_bytes())
    
    info_parser = subparsers.add_parser("info", help="Show container information")
    info_parser.add_argument("file_path", help="Image file container to inspect")
    info_parser.set_defaults(func=info)
    

@register("image", "scramble", description="Pixel scramble an image")
def setup_image_scramble(parser: argparse.ArgumentParser) -> None:
    default_password = os.environ.get("SCRAMBLE_PASSWORD")

    parser.add_argument("file_paths", nargs="+", help="File path(s) to images")
    parser.add_argument(
        "--password",
        "-p",
        default=default_password,
        help="The password to use to scramble, defaults to environment variable SCRAMBLE_PASSWORD",
    )
    parser.add_argument(
        "--unscramble",
        "-u",
        action="store_false",
        dest="do_scramble",
        help="Whether to unscramble instead of scramble",
    )
    parser.add_argument(
        "--out-dir", default=None, help="The directory to save the resulting file to"
    )
    parser.add_argument(
        "--out-format",
        "-f",
        choices=["PNG", "JPEG"],
        default="PNG",
        help="Store the resulting file in this format",
    )
    parser.set_defaults(func=scramble_main)




class CustomImageViewer(ImageViewer):
    def __init__(self, image_file: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(Image.open(image_file), *args, **kwargs)
        self.title = os.path.abspath(image_file)
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield from super().compose()
        yield Footer()
        
    
def show_image(file_path: str) -> None:
    class ImageViewerApp(App):
        def compose(self) -> ComposeResult:
            yield CustomImageViewer(file_path)
    app = ImageViewerApp()
    app.title = os.path.abspath(file_path)
    app.run()
    
    
@register("image", "show", description="Show an image on the CLI")
def setup_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("file_path", help="Path to an image file")
    parser.set_defaults(func=show_image)