# coding: utf-8

"""
Common functions for all formats
"""

from pathlib import Path
from typing import Union, Iterable


EXT_COMP = ('.zip', '.bz2', '.gz', '.bzip', '.bzip2', '.gzip')


class SuffixError(Exception):
    pass


def check_suffix_(path: Union[Path, str], valid: Iterable, default: str, raise_error: bool=False):
    path = Path(path)
    suff = path.suffix.lower()
    if suff in EXT_COMP:
        suff = path.with_suffix('').suffix.lower()
    if suff not in valid:
        if raise_error:
            raise SuffixError(f'file suffix not valid ; should be among: {valid}')
        path = path.with_name(path.name + default)
    return path


def check_type_(data, fmt: str, valid: Iterable=None, raise_error=True):
    if valid is not None:
        if not isinstance(data, valid):
            if raise_error:
                raise TypeError(f'wrong data type for format {fmt} format')
            else:
                return False
    return True
