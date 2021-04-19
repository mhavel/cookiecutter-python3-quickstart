# coding: utf-8

"""
Export file to HDF5 format
"""

from typing import Union
from pathlib import Path

import pandas as pd

from ..utils.serialization import pickle_protocol as set_pickle_protocol
from ..utils.logging import get_sub_logger
from .common import check_suffix_, check_type_


logger = get_sub_logger('io.hdf5')


NAME = 'hdf5'
VALID_EXTENSIONS = ('.hdf', '.hdf5', '.h5')
DEFAULT_EXTENSION = '.hdf5'
DEFAULT_READ_OPTS = {}
DEFAULT_WRITE_OPTS = dict(complevel=6, complib='blosc:zlib', mode='w', key='df')
VALID_TYPES = (pd.DataFrame, pd.Series)


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)


def write(data: pd.DataFrame, path: Union[str, Path], pickle_protocol=None, fix_suffix: bool=True, **kw):
    """
    Write dataframe to HDF5
    """
    check_type(data)
    path = check_suffix(path, raise_error=not fix_suffix)

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    opts = dict(DEFAULT_WRITE_OPTS, **kw)
    if pickle_protocol is not None:
        with set_pickle_protocol(pickle_protocol):
            data.to_hdf(path, key=path.stem, **opts)
    else:
        data.to_hdf(path, key=path.stem, **opts)
    
    logger.info(f'data dumped to HDF5 file: {path}')

    return path


def read(path: Union[str, Path], pickle_protocol=None, fix_suffix: bool=False, **kw):
    """
    Read dataframe from HDF-5
    """
    path = check_suffix(path, raise_error=not fix_suffix)

    opts = dict(DEFAULT_READ_OPTS, **kw)

    if pickle_protocol is not None:
        with set_pickle_protocol(pickle_protocol):
            df = pd.read_hdf(path, **opts)
    else:
        df = pd.read_hdf(path, **opts)
    
    logger.info(f'HDF5 data loaded from: {path}')

    return df
