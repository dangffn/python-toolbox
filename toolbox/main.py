#!/usr/bin/env python3

"""
Main entrypoint to the 'toolbox' CLI tool.
This project contains a collection of CLI based tools.
"""

import argparse
import sys
from importlib import metadata

from toolbox.subcommands.loader import init_subcommands
from toolbox.logger import console_err

__version__ = metadata.version('dans-toolbox')
__author__ = "Dan Griffin"
__maintainer__ = "Dan Griffin"
__email__ = "dangffn@gmail.com"


def run(argv: list[str]):
    """Main entrypoint for the 'toolbox' CLI command.
    """
    parser = argparse.ArgumentParser(prog="toolbox", description="A bunch of commands and stuff")
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Initialize all configured subcommand handlers in the package.
    init_subcommands(parser)

    args = parser.parse_args(argv)
    func = args.__dict__.pop("func", None)
    if not func:
        parser.print_help()
        return 1

    try:
        func(**args.__dict__)
        return 0
    except (ValueError, TypeError, AssertionError, FileNotFoundError) as e:
        console_err.log(f"[red]Error[/red]: {e}")
        return 1


def main():
    return run(sys.argv[1:])
    

if __name__ == "__main__":
    sys.exit(main())
