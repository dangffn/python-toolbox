from typing import overload
from typing import Iterable
from typing import Iterator
import time
import functools
from typing import TypeVar, TypeVar, ParamSpec, Callable, Generator

from toolbox.logger import console
from toolbox.utils import time_delta_string


T = TypeVar("T")
V = TypeVar("V")
P = ParamSpec("P")

IteratorFunc = Callable[P, Iterator[T]]
IterableFunc = Callable[P, Iterable[T]]
GeneratorFunc = Callable[[IterableFunc], IteratorFunc]



def timeit(func: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        delta = time.time() - start
        console.log(f"[green]timeit[/] [white]{func.__name__}[/] took [cyan]{time_delta_string(delta)}[/]")
        return res
    return wrapper


@overload
def timeit_iter(incr: int) -> GeneratorFunc: ...


@overload
def timeit_iter(incr: Callable[P, Iterable[T]]) -> Callable[P, Iterator[T]]: ...


def timeit_iter(incr: Callable[P, Iterable[T]] | int) -> GeneratorFunc | IteratorFunc:
    batch = incr if isinstance(incr, int) else 1

    def inner(func: Callable[P, Iterable[T]]) -> Callable[P, Iterator[T]]:
        _get: Callable[[str], int] = lambda s: getattr(func, s, 0)
        _set: Callable[[str, int], None] = lambda s, n: setattr(func, s, n)

        # Cache the start & total time on the function.
        # Supports multiple calls to the same iterator function.
        setattr(func, "_start", getattr(func, '_start', time.time()))
        setattr(func, "_total", getattr(func, '_total', 0))

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            _iterator = func(*args, **kwargs)
            for idx, res in enumerate(_iterator):
                if idx % batch == 0:
                    total = _get("_total") + idx + 1
                    delta = time.time() - _get("_start")
                    rate = total / delta
                    console.log(f"[green]timeit[/] [white]{func.__name__}[/] rate [cyan]{rate:,.2f}/s[/] total {time_delta_string(delta)}")
                yield res
            _set("_total", _get("_total") + idx + 1)
        return wrapper

    return inner if isinstance(incr, int) else inner(incr)
