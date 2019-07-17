#!/usr/bin/env python3
# coding: utf-8

"""
The main file for the app, dealing with different versions of the API

In order to serve the APP / API using eg. gunicorn, see the file `wsgi.py`
"""

import hug

from . import version, static
from ..pkg.importer import import_obj

app = import_obj(f'api.{version}.app')

hug.API(__name__).extend(static, '/static')
hug.API(__name__).extend(app, f'/{version}')
hug.API(__name__).extend(app, '')

api = hug.API(__name__)
