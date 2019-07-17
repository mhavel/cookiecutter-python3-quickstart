#!/usr/bin/env python3
# coding: utf-8

"""
Package's object importer, using a relative path string
"""
from importlib import import_module

from . import PKG_NAME


def import_obj(path: str):
    """
    Import a (sub-)package / function / variable from this project

    Args:
        path (str): object to be imported from this package (eg. 'pkg_info')

    Notes:
        - first leading '.' in path may be omitted
        - the path is relative to the package's root, always
    """
    if path.startswith('.'):
        path = path[1:]

    p = ''
    o = None
    for e in path.split('.'):
        p += f'.{e}'
        if not e:
            continue
        if hasattr(o, e):
            o = getattr(o, e)
        else:
            o = import_module(p, PKG_NAME)
    return o
