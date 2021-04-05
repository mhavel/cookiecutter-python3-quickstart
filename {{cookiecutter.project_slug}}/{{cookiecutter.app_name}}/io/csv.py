# coding: utf-8

"""
Export file to CSV format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.logging import get_logger


logger = get_logger('{pkg}.io.csv')


VALID_EXTENSIONS = ('.csv', )
DEFAULT_EXTENSION = '.csv'


def check_suffix(path: Union[Path, str]):
    path = Path(path)
    if path.suffix.lower() not in VALID_EXTENSIONS:
        path = path.with_name(path.name + DEFAULT_EXTENSION)
    return path


def write(data: pd.DataFrame, path: Union[str, Path], sep=';'):
    """
    Write dataframe to CSV
    """
    path = check_suffix(path)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    data.to_csv(path, index=False, sep=sep, encoding='utf-8')
    logger.info(f'data exported to CSV file: {path}')

    return path


def read(path: Union[str, Path], sep=';', engine='c', encoding='utf-8'):
    path = check_suffix(path)

    df = pd.read_csv(path, sep=sep, engine=engine, encoding=encoding, low_memory=False)
    logger.info(f'CSV data loaded from: {path}')

    return df
