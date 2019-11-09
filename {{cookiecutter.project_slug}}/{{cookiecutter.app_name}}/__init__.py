#!/usr/bin/env python3
# coding: utf-8

"""
Main entry for package {{cookiecutter.app_name}}
"""

# =====================
#  Package information
# =====================
from .pkg import PKG_NAME, PKG_ROOT
from .pkg.info import *


# ==============
#  Package data
# ==============
from .pkg.data import *


# ================
#  Package config
# ================
# if you need to tune some of the parameters, uncomment the lines below, before importing `.pkg.config`
# from .pkg import params
# from .pkg.data import interpret_resource
# params.DEFAULT_CONFIG_FILE = 'my_config.yml'
# params.BASE_CONFIG = interpret_resource('pkg/data/stopwords.yml')

from .pkg.config import *


# ==================
#  Package importer
# ==================
from .pkg.importer import *
