from pathlib import Path
from PIL import Image
from rich.progress import track

from toolbox.logger import console
from toolbox.utils import multi_file_arg, is_image, new_path_cleanup
from toolbox.subcommands import cli


@cli.register("image", "gif", "extract", positional="gif_file")
def extract_images_from_gif(gif_file: Path | str, out_dir: Path | str="out"):
    """
    Extracts individual frames from a GIF and saves them as separate image files.

    Args:
        gif_file (str): The path to the input GIF file.
        out_dir (str): The folder where the extracted frames will be saved.
    """
    assert Path(gif_file).is_file(), f"{gif_file} is not a file"
    with new_path_cleanup(out_dir, is_file=False) as out_dir:
        with Image.open(gif_file) as im:
            frames = track(range(im.n_frames), description="Extracting frames")
            for frame in frames:
                im.seek(frame)
                file_path = out_dir / f"frame_{frame:04d}.png"
                im.save(file_path)
                
        console.log(f"Wrote [green]{im.n_frames:,}[/] images to [green]{out_dir}[/]")
    
    
@cli.register("image", "gif", "build", positional="file_paths")
def write_gif_from_frames(file_paths: list[Path | str], out_file: str, duration: int=100):
    """
    Creates an animated GIF from image frames in a specified folder.

    Args:
        image_folder (str): Path to the folder containing image frames.
        out_file (str): Path and filename for the output GIF.
        duration (int): Duration of each frame in milliseconds (default is 100ms).
    """
    # Get a sorted list of image file paths
    image_paths = list(filter(is_image, multi_file_arg(*file_paths)))

    assert image_paths, "No images found"
    assert len(image_paths) >= 2, "Specify at least 2 images"
    
    with console.status(f"Loading {len(image_paths):,} images") as status:
        images: list[Image.Image] = []
        for image_path in image_paths:
            status.update(f"Loading [green]{image_path}[/]...")
            images.append(Image.open(image_path))

        status.update(f"Writing GIF [green]{out_file}[/]...")
        images[0].save(
            out_file,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
        )
        
        console.log(f"GIF saved to [green]{out_file}[/green]")