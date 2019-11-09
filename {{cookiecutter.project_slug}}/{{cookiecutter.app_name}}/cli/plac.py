#!/usr/bin/env python3
# coding: utf-8

"""
Tools to use plac in a bit different from official package

In particular, the function `plac_annotations` allows to annotate
a function that does not have named arguments (eg. a function
using only `*args` and `**kwargs`. It also allows for another wrapper to play nicely with `plac`.

The function `plac_call` is intended to be used along with the `Defaults` decorator for a function,
which allows to set default values for the function by reading a JSON file at compilation time.
See `cli.defaults` module.
"""

import inspect
from functools import wraps
import sys

try:
    import plac
    HAS_PLAC = True
except ImportError:
    plac = None
    HAS_PLAC = False


__all__ = ['plac_annotations', 'plac_call', 'plac', 'HAS_PLAC']


def plac_annotations(_wrap=False, **ann):
    """same as `plac.annotations` function, but without any check on the presence of annotated variable names"""
    if _wrap:
        def annotate(func):

            meta = {'is_function': True}

            if callable(_wrap):
                # `_wrap` must be a decorator with one argument: func
                f = _wrap(func)
            else:
                f = func

            func.__annotations__ = ann

            @wraps(func)
            def wrapper(*args, **kwargs):
                if not meta['is_function']:
                    # cls or self is args[0], then args[1] is the useless arg added in order for plac to work properly
                    args = (args[0],) + args[2:]
                return f(*args, **kwargs)
            wrapper._plac_func = func
            wrapper._meta = meta
            return wrapper

    else:
        def annotate(func):
            func.__annotations__ = ann
            return func

    return annotate


def plac_call(obj, arglist=None, eager=True, version=None):
    """
    If obj is a function or a bound method, parse the given arglist
    by using the parser inferred from the annotations of obj
    and call obj with the parsed arguments.
    If obj is an object with attribute .commands, dispatch to the
    associated subparser.
    """
    assert HAS_PLAC, '`plac` package is not available, please install it'
    if hasattr(obj, '_plac_func'):
        # `plac` needs the annotated original function (w/ __annotations__ attributes)
        if arglist is None:
            arglist = sys.argv[1:]
        if not inspect.isfunction(obj):
            arglist = ['_trick_arg0_'] + arglist
            obj._meta['is_function'] = False
        parser = plac.parser_from(obj._plac_func)
        if version:
            parser.add_argument(
                '--version', '-v', action='version', version=version)
        # below: trick so that `plac` will consume the command-line arguments but still use the `defaults` wrapper
        parser.func = obj
        cmd, result = parser.consume(arglist)
        if plac.iterable(result) and eager:  # listify the result
            return list(result)
        return result
    else:
        return plac.call(obj, arglist=arglist, eager=eager, version=version)

