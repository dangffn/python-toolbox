from typing import List
from moviepy import VideoFileClip, concatenate_videoclips

from toolbox.logger import console
from toolbox.utils import multi_file_arg
from toolbox.subcommands import cli


# Uses moviepy (https://github.com/Zulko/moviepy) to merge video clips into a single file.


@cli.register("video", "merge", positional="file_paths")
def merge_video_files(file_paths: List[str], out_file: str="merged.mp4", recursive: bool=False):
    """Merge multiple video files into one.
    
    Args:
        file_paths (list[str]): Video files to merge together
        out_file (str): The output video file to save, default: merged.mp4
        recursive (bool): If specified, search for video files recursively, default: false
    """
    with console.status(f"Merging [green]{len(file_paths)}[/green] video files...") as status:
        video_files = multi_file_arg(*file_paths, recursive=recursive)
        clips = list(map(lambda f: VideoFileClip(f), video_files))

        final_clip = concatenate_videoclips(clips, method="compose")
        
        status.update(f"Writing [green]{out_file}[/green]...")
        final_clip.write_videofile(out_file, codec="libx264", audio_codec="aac")

        for clip in clips:
            clip.close()
