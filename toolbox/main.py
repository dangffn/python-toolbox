#!/usr/bin/env python3

"""
Main entrypoint to the 'toolbox' CLI tool.
This project contains a collection of CLI based tools.
"""

import argparse
import sys

from toolbox.subcommands.loader import init_subcommands
from toolbox.logger import console_err

__version__ = "1.0.0"
__author__ = "Dan Griffin"
__maintainer__ = "Dan Griffin"
__email__ = "dangffn@gmail.com"


def main() -> None:
    """Main entrypoint for the 'toolbox' CLI command.
    """
    parser = argparse.ArgumentParser(description="A bunch of commands and stuff")

    # Initialize all configured subcommand handlers in the package.
    init_subcommands(parser)

    args = parser.parse_args()
    func = args.__dict__.pop("func", None)
    if not func:
        parser.print_help()
        sys.exit(0)

    try:
        func(**args.__dict__)
    except (ValueError, AssertionError) as e:
        console_err.log(f"[red]Error[/red]: {e}")

if __name__ == "__main__":
    main()
