# coding: utf-8

"""
Some reader / writer
"""

from pathlib import Path
from typing import Union, Callable


from . import csv, excel, hdf5, parquet, json, yaml, pickle, joblib
from .common import EXT_COMP


EXT_MODULES = {
    'excel': excel,
}


def get_module(key: str):
    k = key.lower()
    if not k.startswith('.'):
        k = f'.{k}'
    found = False
    for m in (csv, hdf5, excel, json, yaml, pickle, joblib, parquet):
        if k in m.VALID_EXTENSIONS:
            found = True
            break
    if not found:
        if k in EXT_MODULES:
            m = EXT_MODULES[k]
            found = True
    if not found:
        raise ValueError(f'format unsupported for: {key}')
    return m


def update_defaults(fmt: str, read: dict=None, write: dict=None):
    """
    Update default read and / or write options for given IO format (WARNING: not multiprocessing safe)
    """
    m = get_module(fmt)
    if read is not None:
        m.DEFAULT_READ_OPTS.update(read)
    if write is not None:
        m.DEFAULT_WRITE_OPTS.update(write)


def get_output(name: str, root: Union[str, Path]=None, check_suffix: Union[Callable, str]=None, **keywords):
    """
    Get output path given a name, and optionally a root. Can format the name with keywords,
    and check for proper suffix too.
    """
    if isinstance(root, Path):
        root = Path(str(root).format(**keywords)).expanduser()
    elif root is not None:
        root = Path(root.format(**keywords)).expanduser()
    
    if isinstance(name, Path):
        out = Path(str(name).format(**keywords)).expanduser()
    else:
        out = Path(name.format(**keywords)).expanduser()

    if len(out.parts) == 1 and '/' not in name and root is not None:
        out = root / out
    
    if check_suffix is not None:
        if isinstance(check_suffix, str):
            check_suffix = get_module(check_suffix).check_suffix
        return check_suffix(out)
    else:
        return out


def path_and_skey(path: Union[str, Path]):
    p = Path(path).expanduser()
    suff = p.suffix.lower()
    if suff in EXT_COMP:
        suff = p.with_suffix('').suffix.lower()
    return p, suff


def read(path: Union[str, Path], **kw):
    p, s = path_and_skey(path)
    m = get_module(s)
    return m.read(p, fix_suffix=False, **kw)


def write(data, path: Union[str, Path], **kw):
    p, s = path_and_skey(path)
    m = get_module(s)
    if not p.parent.is_dir():
        p.parent.mkdir(parents=True)
    m.write(data, p, fix_suffix=False, **kw)
    return p
