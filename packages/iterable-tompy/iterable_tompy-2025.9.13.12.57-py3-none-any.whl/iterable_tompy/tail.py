from typing import Iterable, Iterator, TypeVar

from .exceptions import InputNotIterableError, EmptyIterableError

T = TypeVar('T')


def tail(iterable: Iterable[T]) -> Iterator:
    try:
        iterator: Iterator = iter(iterable)
    except TypeError as exception:
        raise InputNotIterableError(f"'{iterable}' is not iterable.") from exception

    try:
        _: T = next(iterator)
        tail_items: Iterator = iterator
    except StopIteration as exception:
        raise EmptyIterableError(f"'{iterable}' contains no items.") from exception

    return tail_items
