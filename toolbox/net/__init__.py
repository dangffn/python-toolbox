from toolbox.net.ipv4 import *  # noqa
from toolbox.net.ssh_browser import *  # noqa

from toolbox.subcommands.loader import cli
cli.register_help("net")("Network related commands")