"""Register CLI subcommands on script startup."""
import argparse
from typing import Callable, TypeVar
import docstring_parser
import inspect

from toolbox.utils import find


T = TypeVar("T", bound=Callable)
Func = Callable[[T], T]


class Cli:
    def __init__(self, parser: argparse.ArgumentParser):
        self.parser = parser
        
    def _init_parser(self, subcommand: tuple[str, ...], description: str | None=None) -> argparse.ArgumentParser:
        path = list(subcommand)
        parser = self.parser
        key = tuple()
        
        while path:
            cmd = path.pop(0)
            key += (cmd,)
            
            subp = find(parser._actions, lambda a: isinstance(a, argparse._SubParsersAction))
            subp: argparse._SubParsersAction = subp or parser.add_subparsers(description="Subcommands")

            if not path:
                parser = subp._name_parser_map.get(cmd) or subp.add_parser(cmd, description=description, help=description)
            else:
                parser = subp._name_parser_map.get(cmd) or subp.add_parser(cmd)
            
        return parser
    
    def _get_param_help(self, func: Callable, parameter: str):
        help = ""
        parsed_doc = docstring_parser.parse(func.__doc__)
        for param in parsed_doc.params:
            if param.arg_name == parameter:
                help = param.description
                break
        return help
    
    def _get_func_help(self, func: Callable):
        parsed_doc = docstring_parser.parse(func.__doc__)
        return parsed_doc.short_description
    
    def _add_args_from_func(self, parser: argparse.ArgumentParser, func: Callable, ignores: list[str] | None=None, positional: str | None=None):
        arguments = inspect.signature(func)
        for name, param in arguments.parameters.items():
            if ignores and name in ignores:
                continue
            
            type_ = param.annotation
            try:
                type_str = type_.__name__
            except AttributeError:
                type_str = "str"
            
            kwargs: dict[str, str | bool | type | None] = {
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
            parser.set_defaults(**{ dest: [] })
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
        

parser = argparse.ArgumentParser(description="Dan's Toolbox")
cli = Cli(parser)