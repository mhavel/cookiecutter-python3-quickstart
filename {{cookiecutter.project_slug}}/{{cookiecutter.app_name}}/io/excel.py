# coding: utf-8

"""
Export file to Excel format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.logging import get_sub_logger
from .common import check_suffix_, check_type_


logger = get_sub_logger('io.excel')


NAME = 'excel'
VALID_EXTENSIONS = ('.xls', '.xlsx')
DEFAULT_EXTENSION = '.xlsx'
DEFAULT_READ_OPTS = {}
DEFAULT_WRITE_OPTS = dict(index=False)
VALID_TYPES = (pd.DataFrame, pd.Series)


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)


def write(data: pd.DataFrame, path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Write dataframe to Excel
    """
    check_type(data)
    path = check_suffix(path, raise_error=not fix_suffix)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    opts = dict(DEFAULT_WRITE_OPTS, **kw)

    data.to_excel(path, **opts)
    logger.info(f'data exported to Excel file: {path}')

    return path


def read(path: Union[str, Path], fix_suffix: bool=True, **kw):
    """
    Read dataframe from Excel
    """
    path = check_suffix(path, raise_error=not fix_suffix)

    opts = dict(DEFAULT_READ_OPTS, **kw)

    df = pd.read_excel(path, **opts)
    logger.info(f'Excel data loaded from: {path}')

    return df
