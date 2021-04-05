# coding: utf-8

"""
Export file to Excel format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.logging import get_logger


logger = get_logger('{pkg}.io.excel')


VALID_EXTENSIONS = ('.xls', '.xlsx')
DEFAULT_EXTENSION = '.xlsx'


def check_suffix(path: Union[Path, str]):
    path = Path(path)
    if path.suffix.lower() not in VALID_EXTENSIONS:
        path = path.with_name(path.name + DEFAULT_EXTENSION)
    return path


def write(data: pd.DataFrame, path: Union[str, Path], sheet_name='Sheet1'):
    """
    Write dataframe to Excel
    """
    path = check_suffix(path)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    data.to_excel(path, index=False, sheet_name=sheet_name)
    logger.info(f'data exported to Excel file: {path}')

    return path


def read(path: Union[str, Path], sheet_name=None):
    path = check_suffix(path)

    df = pd.read_excel(path, sheet_name=sheet_name)
    logger.info(f'Excel data loaded from: {path}')

    return df
