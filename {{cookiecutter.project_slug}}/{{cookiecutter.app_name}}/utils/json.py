#!/usr/bin/env python3
# coding: utf-8

"""
JSON tools
"""

# coding=utf-8

"""
Some JSON serialization tools
"""

# import numpy as np
# import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import re


PTYPE = getattr(re, 'Pattern', getattr(re, '_pattern_type', None))  # Py 3.7 introduced the 'Pattern' type
if PTYPE is None:
    # last resort: if above piece of code failed, just extract the type from an actual compiled regexp
    PTYPE = type(re.compile(r'a'))


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


def loads(s, encoding=None, cls=None, **kw):
    return json.loads(s, encoding=encoding, cls=cls, **kw)