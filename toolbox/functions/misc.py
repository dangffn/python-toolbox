from dataclasses import field
from typing import Generic, Iterable, Callable, TypeVar
from dataclasses import dataclass


T = TypeVar("T")


@dataclass
class Group(Generic[T]):
    objects: list[tuple[T, int]] = field(default_factory=list)
    size: int = field(default=0)


def largest_first_distribution(objects: Iterable[T], num_groups: int, func: Callable[[T], int]):
    sizes: Iterable[tuple[T, int]] = map(lambda p: (p, func(p)), objects)
    sizes = sorted(sizes, key=lambda tup: tup[1], reverse=True)

    groups: list[Group[T]] = list(map(lambda n: Group(), range(num_groups)))

    for obj, size in sizes:
        sm: Group[T] = min(groups, key=lambda f: f.size)
        sm.objects.append((obj, size))
        sm.size += size

    for group in sorted(groups, key=lambda g: g.size, reverse=True):
        paths: list[T] = list(map(lambda f: f[0], group.objects))
        if paths:
            yield paths
