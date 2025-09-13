from typing import Callable, Dict, List, Optional, TypeVar, Any
from collections import defaultdict
import argparse


T = TypeVar("T", bound=Callable[..., Any])


registered: Dict[str, List[Callable[..., None]]] = defaultdict(lambda: [])
registered_descriptions: Dict[str, str] = {}


def register(subcommand: str, description: Optional[str]=None) -> Callable[[T], T]:
    def wrapper(func: T) -> T:
        registered[subcommand].append(func)
        if description:
            registered_descriptions[subcommand] = description
        return func
    return wrapper


def init_subcommands(parser: argparse.ArgumentParser) -> None:
    subparsers = parser.add_subparsers()
    for subcommand, setup_commands in registered.items():
        sub_subparsers = subparsers.add_parser(subcommand, help=registered_descriptions.get(subcommand))
        for setup_subparsers in setup_commands:
            setup_subparsers(sub_subparsers)
    