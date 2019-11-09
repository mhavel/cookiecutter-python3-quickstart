#!/usr/bin/env python3
# coding: utf-8

"""
Functions to download file from the web
"""

from pathlib import Path
import requests
import re


def is_downloadable(headers):
    """
    Does the url contain a downloadable resource
    """
    content_type = headers.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def get_filename_from_cd(headers):
    """
    Get filename from content-disposition
    """
    cd = headers.get('content-disposition')
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0]


def download(url, dest=None, name=None, only_binary=True, max_size=None, overwrite=False):
    ok = True
    if only_binary or max_size is not None:
        h = requests.head(url, allow_redirects=True)
        headers = h.headers
        if only_binary:
            ok = is_downloadable(headers)
        if max_size is not None:
            content_length = headers.get('content-length', None)
            ok = content_length < max_size  # in bytes
    if ok:
        req = requests.get(url, allow_redirects=True)
        if name is not None:
            filename = name
        else:
            filename = get_filename_from_cd(req.headers)
        if dest is None:
            dest = Path.cwd() / filename
        else:
            dest = Path(dest).expanduser()
            if dest.exists():
                if dest.is_dir():
                    dest /= filename
                if dest.existst() and not overwrite:
                    raise FileExistsError(f'{dest} already exists: use the `overwrite` argument to download the file'
                                          f' again and overwrite the local copy')
            elif not dest.suffix:
                dest /= filename

            if not dest.parent.is_dir():
                dest.parent.mkdir(parents=True)

        dest.write_bytes(req.content)
        return dest
    else:
        return None
