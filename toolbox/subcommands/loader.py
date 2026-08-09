"""Register CLI subcommands on script startup."""
import argparse
import docstring_parser
import inspect
from typing import Callable, TypeVar, Hashable, Generic, Any

from toolbox.utils import find


T = TypeVar("T", bound=Callable)
P = TypeVar("P", bound=argparse.ArgumentParser)
Func = Callable[[T], T]

class Cli(Generic[P]):
    def __init__(self, parser: P):
        self.parser = parser
        
    def _init_parser(self, subcommand: tuple[str, ...], description: str | None=None) -> P:
        path: list[str] = list(subcommand)
        parser: P = self.parser
        key: tuple[Hashable, ...] = tuple()
        
        while path:
            cmd: str = path.pop(0)
            key += (cmd,)
            
            # find() can return None, but add_subparsers() returns a _SubParsersAction, so subparsers is never None.
            subp_action = find(parser._actions, lambda a: isinstance(a, argparse._SubParsersAction))
            subparsers = subp_action or parser.add_subparsers(description="Subcommands")

            assert isinstance(subparsers, argparse._SubParsersAction), f"Invalid subcommand [{' '.join(map(str, key))}] of type [{type(subparsers)}]"
                
            existing_parser = subparsers._name_parser_map.get(cmd)
            if existing_parser:
                parser = existing_parser
            else:
                parser = subparsers.add_parser(cmd, help=description, description=description)
                
            # Set the parser description if it was not previously set.
            if not path and description:
                parser.description = description
                choice_action = find(subparsers._choices_actions, lambda a: a.dest == cmd)
                if choice_action:
                    choice_action.help = description
            
        return parser
    
    def _get_param_help(self, func: Callable[..., Any], parameter: str) -> str | None:
        help = ""
        parsed_doc = docstring_parser.parse(func.__doc__ or "")
        for param in parsed_doc.params:
            if param.arg_name == parameter:
                help = param.description
                break
        return help or None
    
    def _get_func_help(self, func: Callable[..., Any]) -> str | None:
        parsed_doc = docstring_parser.parse(func.__doc__ or "")
        return parsed_doc.short_description
    
    def _add_args_from_func(self, parser: argparse.ArgumentParser, func: Callable[..., Any], ignores: list[str] | None=None, positional: str | None=None):
        arguments = inspect.signature(func)
        for name, param in arguments.parameters.items():
            if ignores and name in ignores:
                continue
            
            type_ = param.annotation
            try:
                type_str = type_.__name__
            except AttributeError:
                type_str = "str"
            
            kwargs: dict[str, Any] = {
                "help": self._get_param_help(func, name)
            }
            
            is_positional = positional and name == positional
            
            if param.default is not inspect.Parameter.empty:
                kwargs["default"] = param.default
            else:
                if not is_positional:
                    kwargs["required"] = True
            
            if type_str == "list":
                kwargs["nargs"] = "+"
            elif type_str == "bool":
                kwargs["action"] = "store_true"
            elif type_str == "Literal" or type_str == "str":
                kwargs["type"] = str
            else:
                kwargs["type"] = type_
                
            if not is_positional:
                kwargs["dest"] = name
                name = f'--{name.replace("_", "-")}'
                
            try:
                parser.add_argument(name, **kwargs)
            except argparse.ArgumentError:
                pass
    
    def register_arg_const(self, *subcommand: str, dest: str | None=None, ignores: list[str] | None=None, action: str="append_const"):
        def wrapper(func: T) -> T:
            arg_name = func.__name__.replace("_", "-")
            
            parser = self._init_parser(subcommand, self._get_func_help(func))
            parser.add_argument(f"--{arg_name}", dest=dest, action=action, const=func, help=self._get_func_help(func))
            defaults = { dest: [] } if dest else {}
            parser.set_defaults(**defaults)
            self._add_args_from_func(parser, func, ignores)
            return func
        
        return wrapper
        
    def register(self, *subcommand: str, ignores: list[str] | None=None, positional: str | None=None) -> Callable[[T], T]:
        def wrapper(func: T) -> T:
            parser = self._init_parser(subcommand, self._get_func_help(func))
            parser.set_defaults(func=func)
            self._add_args_from_func(parser, func, ignores, positional)

            return func
            
        return wrapper
    
    def register_help(self, *subcommand):
        def wrapper(help: str):
            parser = self._init_parser(subcommand, help)
            parser.set_defaults(func=lambda: parser.print_usage())
        return wrapper
        

parser = argparse.ArgumentParser(description="Dan's Toolbox")
cli = Cli(parser)