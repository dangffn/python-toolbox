import os
from typing import List
from moviepy import VideoFileClip, concatenate_videoclips

from toolbox.logger import console


# Uses moviepy (https://github.com/Zulko/moviepy) to merge video clips into a single file.


def merge_video_files(video_filenames: List[str], output_filename: str="merged.mp4"):
    assert video_filenames, "No video files specified to merge"
    for file in video_filenames:
        assert os.path.isfile(file), f"File {file} does not exist"

    with console.status(f"Merging [green]{len(video_filenames)}[/green] video files...") as status:
        clips = list(map(lambda f: VideoFileClip(f), video_filenames))

        final_clip = concatenate_videoclips(clips, method="compose")
        
        status.update(f"Writing [green]{output_filename}[/green]...")
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")

        for clip in clips:
            clip.close()
