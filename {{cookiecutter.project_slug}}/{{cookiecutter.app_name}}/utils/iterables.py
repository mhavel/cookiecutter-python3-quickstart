# coding: utf-8


from itertools import combinations_with_replacement, combinations
from functools import reduce
import operator


def combinations_of(iterable) -> list:
    return reduce(operator.add, (list(combinations(iterable, i+1)) for i, _ in enumerate(iterable)), [])


def combinations_with_replacement_of(iterable) -> list:
    return reduce(operator.add, (list(combinations_with_replacement(iterable, i+1)) for i, _ in enumerate(iterable)), [])
