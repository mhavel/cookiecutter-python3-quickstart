#!/usr/bin/env python3
# coding: utf-8

"""
JSON tools
"""

# import numpy as np
# import pandas as pd
from typing import Union
import json
from datetime import datetime
from pathlib import Path
import re

from .common import check_type_, check_suffix_


NAME = 'json'
VALID_EXTENSIONS = ('.json', )
DEFAULT_EXTENSION = '.json'
VALID_TYPES = None


PTYPE = getattr(re, 'Pattern', getattr(re, '_pattern_type', None))  # Py 3.7 introduced the 'Pattern' type
if PTYPE is None:
    # last resort: if above piece of code failed, just extract the type from an actual compiled regexp
    PTYPE = type(re.compile(r'a'))


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)



class ExtendedJSONEncoder(json.JSONEncoder):
    """usage:

    json.dumps(data, cls=ExtendedJSONEncoder)
    """
    def default(self, o):
        if isinstance(o, set):
            return list(o)
        elif isinstance(o, datetime):
            # datetime object
            return str(o)
        elif isinstance(o, PTYPE):
            # re compiled expression
            return {'expr': o.pattern, 'flags': o.flags}
        elif isinstance(o, Path):
            # Path
            return str(o)
        elif hasattr(o, 'tolist'):
            # eg. numpy.ndarray, pandas.Series
            return o.tolist()
        elif hasattr(o, 'to_dict'):
            # eg. pandas.DataFrame
            return o.to_dict(orient='list')
        elif hasattr(o, 'values'):
            # eg. pandas.Series
            return o.values
        elif hasattr(o, 'dtype'):
            # eg. numpy.float32, numpy.int32, ...
            k = o.dtype.kind
            if k == 'f':
                return float(o)
            elif k == 'i':
                return int(o)
            elif k == 'b':
                return bool(o)
        else:
            return super().default(o)


def dumps(data, indent=2, ensure_ascii=False, cls=ExtendedJSONEncoder, **kw):
    return json.dumps(data, cls=cls, indent=indent, ensure_ascii=ensure_ascii, **kw)


def loads(s, cls=None, **kw):
    return json.loads(s, cls=cls, **kw)


def read(path: Union[str, Path], container=None, fix_suffix: bool=True, **kw):
    path = check_suffix(path, raise_error=not fix_suffix)
    data = loads(path.read_text(), **kw)
    if container is not None:
        data = container(data)
    return data


def write(x, path: Union[str, Path], fix_suffix: bool=True, **kw):
    path = check_suffix(path, raise_error=not fix_suffix)
    return path.write_text(dumps(x, **kw))