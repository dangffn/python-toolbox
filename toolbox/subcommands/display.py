"""Display related utils.
"""
import argparse
import os
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual_imageview.viewer import ImageViewer
from PIL import Image

from toolbox.subcommands.loader import register


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
    
    
@register("display", description="Display related utils")
def setup_parser(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers()
    show_parser = subparsers.add_parser("show", help="View images in the terminal")
    show_parser.add_argument("file_path", help="Path to an image file")
    show_parser.set_defaults(func=show_image)