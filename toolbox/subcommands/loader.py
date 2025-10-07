"""Register CLI subcommands on script startup."""
from typing import Callable, Dict, List, Optional, TypeVar, Any
from collections import defaultdict
import argparse


T = TypeVar("T", bound=Callable[..., Any])


registered: Dict[str, List[Callable[..., None]]] = defaultdict(lambda: [])
registered_descriptions: Dict[str, str] = {}


def register(subcommand: str, description: Optional[str]=None) -> Callable[[T], T]:
    """Decorates a subcommand handler method. Decorated methods will be loaded on startup and
    registered to the appropriate CLI 'subcommand' in the argparse subparsers.

    Args:
        subcommand (str): CLI subcommand to register the method to
        description (Optional[str], optional): Optional description used in '--help'. Defaults to
        None.

    Returns:
        Callable[[T], T]: decorated method used as the CLI subcommand handler.
    """
    def wrapper(func: T) -> T:
        registered[subcommand].append(func)
        if description:
            registered_descriptions[subcommand] = description
        return func
    return wrapper


def init_subcommands(parser: argparse.ArgumentParser) -> None:
    """Initialize all of the registered subcommand handlers. Inserting them into the main argparse
    argument parser config.

    Args:
        parser (argparse.ArgumentParser): argument parser instance to register subcommands
    """
    subparsers = parser.add_subparsers()
    for subcommand, setup_commands in registered.items():
        sub_subparsers = subparsers.add_parser(subcommand, help=registered_descriptions.get(subcommand))
        for setup_subparsers in setup_commands:
            setup_subparsers(sub_subparsers)
