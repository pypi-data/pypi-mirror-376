from typing import Iterable, Iterator, TypeVar

from .exceptions import InputNotIterableError, EmptyIterableError

T = TypeVar('T')


def last_iterator(iterator: Iterator[T], current: T) -> T:
    for upcoming in iterator:
        current = upcoming
    return current


def last(iterable: Iterable[T]) -> T:
    try:
        last_items: Iterator[T] = iter(iterable)
    except TypeError as exception:
        raise InputNotIterableError(f"'{iterable}' is not iterable.") from exception

    try:
        current: T = next(last_items)
    except StopIteration as exception:
        raise EmptyIterableError(f"'{iterable}' contains no items.") from exception
    else:
        iterator: Iterator[T] = last_iterator(iterator=last_items, current=current)

    return iterator
