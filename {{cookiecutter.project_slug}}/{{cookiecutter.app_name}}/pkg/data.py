#!/usr/bin/env python3
# coding: utf-8

"""
Package's data / resources utils
"""
from pkg_resources import resource_filename
from pathlib import Path
import shutil

from . import PKG_NAME, PKG_DATA_ROOT


_TEXT_EXT = (
    '.txt',
    '.json',
    '.jsonl',
    '.csv',
    '.yml',
    '.yaml',
    '.js',
    '.html',
    '.css',
    '.md'
)


# =======================================
#  Resources outside package's structure
# =======================================
# typically defined by 'data_files' and/or MANIFEST.in in setuptools
def get_data_file(path):
    """return the Path instance of the desired data file"""
    # if not path.startswith('share/{{cookiecutter.app_name}}'):
    #     path = 'share/{{cookiecutter.app_name}}/' + path
    return PKG_DATA_ROOT / path


def read_data_file(path, as_bytes=None, encoding='utf-8', loader=None, on_missing=None):
    p = get_data_file(path)
    if not p.is_file():
        if on_missing is None:
            raise FileNotFoundError(f'package data file {p} not readable or does not exit')
        else:
            if callable(on_missing):
                return on_missing()
            elif isinstance(on_missing, (str, bytes)):
                if loader is not None:
                    return loader(on_missing)
                else:
                    return on_missing
            else:
                return on_missing
    if as_bytes is None:
        sl = p.suffix.lower()
        as_bytes = sl not in _TEXT_EXT
    if as_bytes:
        dat = p.read_bytes()
    else:
        dat = p.read_text(encoding=encoding)

    if loader is not None:
        return loader(dat)
    else:
        return dat


def copy_data_file(path, dest, pattern='*'):
    """Copy a resource file to another destination"""
    src = get_data_file(path)
    dest = Path(dest).expanduser().absolute()

    if src.is_file():
        if dest.is_dir():
            dest /= src.name
        elif not dest.exists():
            if not dest.suffix:
                dest /= src.name
        shutil.copy2(str(src), str(dest))

        return src

    else:
        if not dest.is_dir():
            assert not dest.exists(), '`dest` must be a directory, eventually not existing: cannot copy dir. data'
            dest.mkdir(parents=True)

        files = src.glob(pattern)
        for name in files:
            shutil.copy2(str(name), str(dest / name.name), follow_symlinks=False)

        return files


# ======================================
#  Resources within package's structure
# ======================================
# typically defined by 'package_data' in setuptools
def get_resource(path):
    """Return the Path instance of the desired resource file"""
    # if not path.startswith('data/'):
    #     path = 'data/' + path
    return Path(resource_filename(PKG_NAME, path))


def read_resource(path, as_bytes=None, encoding='utf-8'):
    """
    Read the resource file, eventually as bytes instead of text string (default to unicode)
    """
    p = get_resource(path)
    if as_bytes is None:
        sl = p.suffix.lower()
        as_bytes = sl not in _TEXT_EXT
    if as_bytes:
        return p.read_bytes()
    else:
        return p.read_text(encoding=encoding)


def copy_resource(path, dest, pattern='*'):
    """Copy a resource file to another destination"""
    src = get_resource(path)
    dest = Path(dest).expanduser().absolute()

    if src.is_file():
        if dest.is_dir():
            dest /= src.name
        elif not dest.exists():
            if not dest.suffix:
                dest /= src.name
        shutil.copy2(str(src), str(dest))

        return src

    else:
        if not dest.is_dir():
            assert not dest.exists(), '`dest` must be a directory, eventually not existing: cannot copy dir. resource'
            dest.mkdir(parents=True)

        files = src.glob(pattern)
        for name in files:
            shutil.copy2(str(name), str(dest / name.name), follow_symlinks=False)

        return files
