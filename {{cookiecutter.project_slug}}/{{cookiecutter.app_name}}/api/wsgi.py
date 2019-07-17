#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example using gunicorn (executed where this file or one of its symbolic link is present):
> gunicorn wsgi:server
"""

from {{cookiecutter.app_name}}.api.app import api

server = api.http.server()
