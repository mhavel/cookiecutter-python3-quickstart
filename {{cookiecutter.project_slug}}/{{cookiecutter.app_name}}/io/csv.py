# coding: utf-8

"""
Export file to CSV format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.logging import get_sub_logger
from .common import check_suffix_, check_type_


logger = get_sub_logger('io.csv')


NAME = 'csv'
VALID_EXTENSIONS = ('.csv', )
DEFAULT_EXTENSION = '.csv'
DEFAULT_READ_OPTS = dict(engine='c', sep=';', low_memory=False, encoding='utf-8')
DEFAULT_WRITE_OPTS = dict(sep=';', index=False, encoding='utf-8')
VALID_TYPES = (pd.DataFrame, pd.Series)


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)


def write(data: pd.DataFrame, path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Write dataframe to CSV
    """
    check_type(data)
    path = check_suffix(path, raise_error=not fix_suffix)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    opts = dict(DEFAULT_WRITE_OPTS, **kw)

    data.to_csv(path, **opts)
    logger.info(f'data exported to CSV file: {path}')

    return path


def read(path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Read dataframe from CSV
    """
    path = check_suffix(path, raise_error=not fix_suffix)

    opts = dict(DEFAULT_READ_OPTS, **kw)

    df = pd.read_csv(path, **opts)
    logger.info(f'CSV data loaded from: {path}')

    return df
