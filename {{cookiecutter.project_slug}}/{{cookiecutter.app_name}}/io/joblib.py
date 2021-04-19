# coding: utf-8

"""
Pickle object, using joblib
"""

from typing import Union
from pathlib import Path

import pandas as pd
import joblib

from ..utils.logging import get_sub_logger
from .common import check_suffix_, check_type_


logger = get_sub_logger('io.joblib')


NAME = 'joblib'
VALID_EXTENSIONS = ('.jpkl', '.joblib')
DEFAULT_EXTENSION = '.jpkl'
DEFAULT_READ_OPTS = {}
DEFAULT_WRITE_OPTS = dict(compress=True)
VALID_TYPES = None


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)


def write(data: pd.DataFrame, path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Pickle data to file
    """
    check_type(data)
    path = check_suffix(path, raise_error=not fix_suffix)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    opts = dict(DEFAULT_WRITE_OPTS, **kw)
    joblib.dump(data, path, **opts)

    logger.info(f'data exported to joblib file: {path}')

    return path


def read(path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Un-pickle data from file
    """
    path = check_suffix(path, raise_error=not fix_suffix)

    opts = dict(DEFAULT_READ_OPTS, **kw)
    x = joblib.load(path, **opts)

    logger.info(f'joblib data loaded from: {path}')

    return x
