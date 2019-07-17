#!/usr/bin/env python3
# coding: utf-8

"""

"""

import hug

from ...utils.augmented import AugmentedDict
from ..html import render

get = hug.get(on_invalid=hug.redirect.not_found)
post = hug.post(output=hug.output_format.json)
html = hug.get(output=hug.output_format.html)

CONT = AugmentedDict()


@hug.startup()
def init(*args, **kwargs):
    # init things here. Usually useful to put stuff in the global container CONT
    # eg. CONT.key = value
    pass


@html.urls('/')
def home_page():
    """Home page"""
    return render('default')

