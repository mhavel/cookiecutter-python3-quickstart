#!/usr/bin/env python3
# coding: utf-8

"""
Functions to read files, Agnostic to where the file's is
"""

from pathlib import Path
import srsly
# import yaml

from ..utils import yaml


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


# YAML C loader only available when libyaml is installed
# YamlLoader = getattr(yaml, 'CLoader', yaml.Loader)


def read_yaml(x):
    if isinstance(x, bytes):
        pass
    elif isinstance(x, Path):
        x = x.read_bytes()
    else:
        assert isinstance(x, str)
        s = x[-10:].lower()
        if s.endswith('.yml') or s.endswith('.yaml'):
            p = Path(x).expanduser().resolve()
            if p.is_file():
                x = p.read_bytes()
            else:
                raise ValueError(f'this is not a valid YAML file path: {p}')
    # return yaml.load(x, Loader=YamlLoader)
    return yaml.load(x)


def read_file(path, as_bytes=None, encoding='utf-8', loader=None, reader=None, on_missing=None):
    """Read a file's content either as a simple string / bytes, or using the given loader function which takes the
    read str/bytes as input"""
    p = Path(path).expanduser().resolve()
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
    if reader is not None:
        assert callable(reader)
        dat = reader(p)
    elif as_bytes:
        dat = p.read_bytes()
    else:
        dat = p.read_text(encoding=encoding)

    if loader is not None and reader is None:
        return loader(dat)
    else:
        return dat


def interpret_file(path, encoding='utf-8', readers: dict=None):
    """Read a file's using the proper loader from the extension"""
    path = Path(path).expanduser().resolve()
    s = path.suffix.lower()
    if readers is None:
        readers = {}
    elif not isinstance(readers, dict):
        assert callable(readers)
        readers = {s: readers}
    if s in readers:
        func = readers[s]
        assert callable(func)
        return func(path)
    elif s == '.json':
        return srsly.read_json(path)
    elif s == '.jsonl':
        return srsly.read_jsonl(path)
    elif s in ('.yml', '.yaml'):
        # return yaml.load(path.read_bytes(), Loader=YamlLoader)
        return yaml.load(path.read_bytes())
    elif s in ('.pkl', '.bin', '.pickle'):
        return srsly.pickle_loads(path.read_text(encoding=encoding))
    elif s not in _TEXT_EXT:
        return path.read_bytes()
    else:
        return path.read_text(encoding=encoding)
