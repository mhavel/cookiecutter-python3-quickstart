#!/usr/bin/env python3
# coding: utf-8

"""
Parameters intended to be used / modified by the end-user (so that there should be not need to modify directly
`data.py` or `config.py`

Modify these parameters in your package's root `__init__.py` file, before loading `pkg.config`
"""

from .data import interpret_resource


DEFAULT_CONFIG_FILE = '{{cookiecutter.app_name}}.yml'
BASE_CONFIG = None   # eg with package's resource file: interpret_resource('pkg/data/myconfig.yml')
INSTALL_CONFIG_FILE = '{{cookiecutter.app_name}}.yml'   # use None to disable use of installed data config file, or change the target's name
CREATE_USER_CONFIG_IF_NONE = True
