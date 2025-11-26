import argparse

from toolbox.subcommands.loader import register
from toolbox.video.merge import merge_video_files


@register("video", description="Video related utilities")
def setup_video(parser: argparse.ArgumentParser) -> None:
    parser.set_defaults(func=parser.print_help)


@register("video", "merge", description="Merge multiple video files into one")
def merge_video_files_cmd(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("video_filenames", nargs="+", help="Video files to merge")
    parser.add_argument("--output-filename", default="output.mp4", help="The output filename for the merged video")
    parser.set_defaults(func=merge_video_files)
