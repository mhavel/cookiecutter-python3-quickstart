#!/usr/bin/env python3
# coding: utf-8

"""
Package's utils
"""

from pathlib import Path
import sys
import site


PKG_ROOT = Path(__file__).resolve().parent.parent
PKG_NAME = PKG_ROOT.name

# check what is the type of installation: develop, default (sys.prefix), user (site.USER_BASE)
if (PKG_ROOT.parent / 'setup.py').is_file():
    # >> develop (setup.py found ; package under {{cookiecutter.app_name}})
    PKG_DATA_ROOT = PKG_ROOT.parent
elif str(PKG_ROOT).startswith(sys.prefix):
    # >> default (package installed under sys.prefix)
    PKG_DATA_ROOT = Path(sys.prefix)
else:
    # >> user
    PKG_DATA_ROOT = Path(site.USER_BASE) / f'share/{PKG_NAME}'
