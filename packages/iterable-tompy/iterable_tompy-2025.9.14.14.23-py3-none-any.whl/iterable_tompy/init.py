from typing import Iterable, Iterator, TypeVar

from .exceptions import InputNotIterableError

T = TypeVar('T')


def init_iterator(iterator: Iterator[T], previous: T) -> Iterator[T]:
    while True:
        try:
            current: T = next(iterator)
        except StopIteration:
            break
        else:
            yield previous
            previous = current


def init(iterable: Iterable[T]) -> Iterator[T]:
    try:
        init_items: Iterator[T] = iter(iterable)
    except TypeError as exception:
        raise InputNotIterableError(f"'{iterable}' is not iterable.") from exception

    try:
        previous: T = next(init_items)
    except StopIteration:
        iterator: Iterator[T] = iter(())
    else:
        iterator: Iterator[T] = init_iterator(iterator=init_items, previous=previous)

    return iterator
