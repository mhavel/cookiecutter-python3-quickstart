#!/usr/bin/env python3
# coding: utf-8

"""
Render Jinja2 HTML templates
"""

from jinja2 import Environment, PackageLoader, select_autoescape

from ..pkg.data import PKG_NAME


Loader = PackageLoader(PKG_NAME, 'api/templates')

env = Environment(loader=Loader, autoescape=select_autoescape(['html', 'xml']))


def render(name, **kwargs):
    t = env.get_template(f'{name}.jinja2')
    return t.render(**kwargs)
