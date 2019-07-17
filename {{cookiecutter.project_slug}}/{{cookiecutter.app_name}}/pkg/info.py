#!/usr/bin/env python3
# coding: utf-8

"""

"""

from . import PKG_NAME, PKG_ROOT
from .data import read_data_file

__all__ = ['__author__', '__date__', '__contact__', '__version__', '__website__', 'version', 'root', 'pkg_info']


def get_version():
    return read_data_file('VERSION', as_bytes=False).splitlines()[0]


def get_date():
    return read_data_file('DATE', as_bytes=False).splitlines()[0]


__author__ = '{{cookiecutter.author_name}}'
__date__ = get_date()
__contact__ = '{{cookiecutter.author_email}}'
__version__ = get_version()
__website__ = '{{cookiecutter.project_url}}'
__license__ = 'MIT'


version = __version__
root = PKG_ROOT


pkg_info = {
    'date': __date__,
    'author': __author__,
    'contact': __contact__,
    'version': __version__,
    'website': __website__,
    'root': root,
    'name': PKG_NAME
}
