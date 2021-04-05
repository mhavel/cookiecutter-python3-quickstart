# coding: utf-8

"""
Export file to HDF5 format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.serialization import pickle_protocol as set_pickle_protocol
from ..utils.logging import get_logger


logger = get_logger('{pkg}.io.hdf5')


VALID_EXTENSIONS = ('.hdf', '.hdf5')
DEFAULT_EXTENSION = '.hdf5'

DEFAULT_COMPLEVEL = 6
DEFAULT_COMPLIB = 'blosc:zlib'


def check_suffix(path: Union[Path, str]):
    path = Path(path)
    if path.suffix.lower() not in VALID_EXTENSIONS:
        path = path.with_name(path.name + DEFAULT_EXTENSION)
    return path


def write(data: pd.DataFrame, path: Union[str, Path], mode='w', compression=True, pickle_protocol=None):
    """
    Write dataframe to HDF5
    """
    path = check_suffix(path)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    if compression:
        if isinstance(compression, bool):
            complevel = DEFAULT_COMPLEVEL
            complib = DEFAULT_COMPLIB
        elif isinstance(int):
            complevel = compression
            complib = DEFAULT_COMPLIB
        elif isinstance(str):
            complevel = DEFAULT_COMPLEVEL
            complib = compression
        else:
            assert isinstance(compression, (list, tuple))
            complevel, complib = compression[:2]
    else:
        complevel = complib = None

    if pickle_protocol is not None:
        with set_pickle_protocol(pickle_protocol):
            data.to_hdf(path, key=path.stem, mode=mode, complevel=complevel, complib=complib)
    else:
        data.to_hdf(path, key=path.stem, mode=mode, complevel=complevel, complib=complib)
    logger.info(f'data dumped to HDF5 file: {path}')

    return path


def read(path: Union[str, Path], pickle_protocol=None):
    path = check_suffix(path)

    if pickle_protocol is not None:
        with set_pickle_protocol(pickle_protocol):
            df = pd.read_hdf(path)
    else:
        df = pd.read_hdf(path)
    logger.info(f'HDF5 data loaded from: {path}')

    return df
