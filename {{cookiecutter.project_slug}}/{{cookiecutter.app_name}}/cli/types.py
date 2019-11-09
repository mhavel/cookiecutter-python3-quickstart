#!/usr/bin/env python3
# coding: utf-8

"""
Functions to help transform a CLI string input to a proper type

Useful for `argparse` or `plac` cli interpreters
"""

from pathlib import Path


# -- type functions --
def dict_or_str(x: str):
    x = x.strip()
    if x.startswith('{'):
        x = eval(x, {}, {})
    return x


def list_or_str(x: str):
    x = x.strip()
    if x[0] in ('(', '['):
        x = eval(x, {}, {})
    return x


def smart_bool(x: str):
    x = x.strip()
    if x.lower() in ('yes', 'y', '1', 'true', 't', 'on'):
        return True
    else:
        return False


def smart_bool_or_str(x: str):
    x = x.strip()
    _x = x.lower()
    if _x in ('yes', 'y', '1', 'true', 't', 'on'):
        return True
    elif _x in ('no', 'n', '0', 'false', 'f', 'off'):
        return False
    else:
        return x


def path_type(x: str):
    return Path(x).expanduser()


def abs_path_type(x: str):
    return Path(x).expanduser().resolve()


def path_type_default_file(filename: str):
    def _path_type(x: str):
        p = path_type(x)
        if p.is_dir():
            p /= filename
        return p
    return _path_type


def str2list(sep=','):
    def _str2list(x: str):
        return list(map(str.strip, x.split(sep)))
    return _str2list
