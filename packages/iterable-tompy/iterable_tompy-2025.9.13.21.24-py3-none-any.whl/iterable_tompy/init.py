from typing import Iterable, Iterator, TypeVar

from .exceptions import InputNotIterableError, EmptyIterableError

T = TypeVar('T')


def init(iterable: Iterable[T]) -> Iterator[T]:
    # Not suitable for large sequences or streams, as iterable is materialized twice (!) to enable double reversal!

    try:
        reversed_: Iterator[T] = reversed(list(iterable))
        _: T = next(reversed_)
        re_reversed_: Iterator[T] = reversed(list(reversed_))
        iterator: Iterator[T] = iter(re_reversed_)
        init_items: Iterator[T] = iterator
    except TypeError as exception:
        raise InputNotIterableError(f"'{iterable}' is not iterable.") from exception
    except StopIteration as exception:
        raise EmptyIterableError(f"'{iterable}' contains no items.") from exception

    return init_items
