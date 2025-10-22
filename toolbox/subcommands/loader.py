"""Register CLI subcommands on script startup."""
from typing import Callable, Dict, Union, List, Optional, TypeVar, TypedDict, Any
from collections import defaultdict
import argparse

Func = Callable[[argparse.ArgumentParser], None]

Registered = TypedDict("Registered", {
    "func": Func,
    "children": Dict[str, "Registered"],
})

T = TypeVar("T", bound=Func)


def get_default() -> Registered:
    return { "func": lambda x: None, "children": defaultdict(get_default) }


registered: Dict[str, Registered] = defaultdict(get_default)


def register(*subcommand: str, description: Optional[str]=None) -> Callable[[T], T]:
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
        setattr(func, "_description", description)
        
        path: List[str] = list(subcommand)
        cmd = path[0]
        reg: Dict[str, Registered] = registered
        
        while len(path) > 1:
            reg = reg[path.pop(0)]["children"]
            cmd = path[0]
            
        reg[cmd]["func"] = func
        return func
    return wrapper


def init_subcommands(parser: argparse.ArgumentParser, reg: Optional[Dict[str, Registered]] = None) -> None:
    """Initialize all of the registered subcommand handlers. Inserting them into the main argparse
    argument parser config.

    Args:
        parser (argparse.ArgumentParser): argument parser instance to register subcommands
    """
    if reg is None:
        reg = registered
        
    if not reg:
        return
    
    subparsers = parser.add_subparsers()
    
    for subcommand, child in reg.items():
        sub_subparsers = subparsers.add_parser(subcommand, help=getattr(child["func"], "_description", None))
        child["func"](sub_subparsers)
        init_subcommands(sub_subparsers, child["children"])
