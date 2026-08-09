from toolbox.image.scramble import *  # noqa
from toolbox.image.stego import *  # noqa
from toolbox.image.convert import *  # noqa
from toolbox.image.info import *  # noqa
from toolbox.image.gif import *  # noqa

from toolbox.subcommands.loader import cli
cli.register_help("image")("Image manipulation commands")
