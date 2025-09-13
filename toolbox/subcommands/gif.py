import glob
import os
import argparse
from PIL import Image
from rich.progress import track

from toolbox.subcommands.loader import register
from toolbox.logger import console, console_err

def extract_images_from_gif(gif_file: str, out_folder: str="out") -> bool:
    """
    Extracts individual frames from a GIF and saves them as separate image files.

    Args:
        gif_file (str): The path to the input GIF file.
        out_folder (str): The folder where the extracted frames will be saved.
    """
    try:
        out_folder = os.path.abspath(out_folder)
        os.makedirs(out_folder, exist_ok=True)
        with Image.open(gif_file) as im:
            for i in track(range(im.n_frames), description="Extracting frames"):
                im.seek(i)
                frame_filename = os.path.join(out_folder, f"frame_{i:04d}.png")
                im.save(frame_filename)
            console.log(f"Wrote [green]{im.n_frames}[/green] images to [green]{out_folder}[/green]")
        return True
        
    except FileNotFoundError:
        console_err.log(f"Error: GIF file not found at {gif_file}", style="red")
    except Exception as e:
        console_err.log(f"An error occurred: {e}", style="red")
    return False
        
def write_gif_from_frames(image_folder: str, out_file: str, duration: int=100) -> bool:
    """
    Creates an animated GIF from image frames in a specified folder.

    Args:
        image_folder (str): Path to the folder containing image frames.
        out_file (str): Path and filename for the output GIF.
        duration (int): Duration of each frame in milliseconds (default is 100ms).
    """
    # Get a sorted list of image file paths
    image_paths = sorted(glob.glob(f"{image_folder}/*.png"))

    if not image_paths:
        console_err.log(f"No images found in {image_folder}", style="red")
        return False

    # Open all image frames
    images = [Image.open(path) for path in image_paths]
    
    out_file = os.path.abspath(out_file)

    # Save as GIF
    # The first image is saved, and subsequent images are appended
    with console.status(f"Writing image [green]{out_file}[/green]"):
        images[0].save(
            out_file,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0
        )
    console.log(f"GIF saved to [green]{out_file}[/green]")
    return True

@register("gif", description="Create and extract GIF images")
def setup_subparsers(parser: argparse.ArgumentParser) -> None:
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
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gif extract & build")
    subparsers = parser.add_subparsers(help="Subcommands")
    setup_subparsers(subparsers)
    
    args = parser.parse_args()
    func = args.__dict__.pop("func")
    func(**args.__dict__)
