from pathlib import Path

from PIL import Image
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header
from textual_imageview.viewer import ImageViewer  # pyright: ignore[reportMissingTypeStubs]

from toolbox import utils
from toolbox.logger import console_err
from toolbox.subcommands import cli


class ImageViewerApp(App[None]):
    """Textual app for browsing a list of images, navigable with the arrow keys."""

    CSS = """
    #viewer {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("left", "prev", "Previous"),
        Binding("right", "next", "Next"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, files: list[Path]) -> None:
        super().__init__()
        self.files = files
        self.index = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="viewer")
        yield Footer()

    def on_mount(self) -> None:
        self.show_image(0)

    def show_image(self, index: int) -> None:
        """Replace the current viewer with the image at `index` (wraps around)."""
        self.index = index % len(self.files)
        path = self.files[self.index]

        container = self.query_one("#viewer", Container)
        container.remove_children()
        container.mount(ImageViewer(Image.open(path)))

        self.title = str(path.resolve())
        self.sub_title = f"{self.index + 1}/{len(self.files)}"

    def action_prev(self) -> None:
        self.show_image(self.index - 1)

    def action_next(self) -> None:
        self.show_image(self.index + 1)


@cli.register("image", "view", positional="file_paths")
def view_image(file_paths: list[str]) -> None:
    """View images in the terminal. Use left/right arrows to navigate, scroll to zoom, drag to pan.

    Args:
        file_paths (list[str]): image files, or a directory of images, to view
    """
    files = list(filter(utils.is_image, utils.multi_file_arg(*file_paths)))
    if not files:
        console_err.print("[red]No image files found[/]")
        return

    ImageViewerApp(files).run()
