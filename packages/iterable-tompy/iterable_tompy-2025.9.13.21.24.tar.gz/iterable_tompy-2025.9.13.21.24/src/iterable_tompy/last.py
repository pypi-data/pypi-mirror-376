from typing import Iterable, Iterator, TypeVar

from .exceptions import InputNotIterableError, EmptyIterableError

T = TypeVar('T')


def last(iterable: Iterable[T]) -> T:
    # Not suitable for large sequences or streams, as iterable is materialized to enable reversal!

    try:
        reversed_: Iterator[T] = reversed(list(iterable))
        iterator: Iterator[T] = iter(reversed_)
    except TypeError as exception:
        raise InputNotIterableError(f"'{iterable}' is not iterable.") from exception

    try:
        first_item: T = next(iterator)
    except StopIteration as exception:
        raise EmptyIterableError(f"'{iterable}' contains no items.") from exception

    return first_item
