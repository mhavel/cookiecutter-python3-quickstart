#!/usr/bin/env python3
# coding: utf-8

"""
Serve static files
"""

import hug

from ..pkg.data import get_resource


suffix_output = hug.output_format.suffix({
    '.js': hug.output_format.file,
    '.map': hug.output_format.file,
    '.css': hug.output_format.file,
    '.png': hug.output_format.image('png'),
    '.jpg': hug.output_format.image('jpg'),
    '.jpeg': hug.output_format.image('jpeg'),
    '.ico': hug.output_format.image('ico'),
    '.svg': hug.output_format.image('svg'),
})


@hug.get('/{name}', output=suffix_output)
def static(name, response):
    response.set_header('Content-Disposition', f'inline; filename="{name}"')
    return str(get_resource(f'api/static/{name}'))
