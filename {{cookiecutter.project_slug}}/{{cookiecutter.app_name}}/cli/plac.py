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

 
class PlacCommand:
    def __init__(self, func: callable, annotations: dict, strict: bool=True, wrap: (bool, callable)=False, name: str=None, desc: str=None):
        self.func = func
        self.annotations = ann = self.make_annotations(annotations)
        if strict:
            self.plac_func = plac.annotations(**ann)(func)
        else:
            self.plac_func = plac_annotations(wrap, **ann)(func)

        if name is None:
            name = func.__name__
        self.name = name

        if desc is None:
            if func.__doc__ is not None and func.__doc__:
                desc = func.__doc__
            else:
                desc = f'command `{name}` (no description)'
        self.desc = desc
        self.plac_func.__doc__ = desc

    @staticmethod
    def ann(*a, **kw):
        """Return a plac.Annotation instance"""
        return plac.Annotation(*a, **kw)

    @staticmethod
    def make_annotations(ann: dict):
        r = {}
        for k, v in ann.items():
            if isinstance(v, dict):
                r[k] = plac.Annotation(**v)
            elif isinstance(v, (tuple, list)):
                r[k] = plac.Annotation(*v)
            else:
                r[k] = v
        return r

    def call(self, arglist=None, eager=True, version=None):
        if arglist is None:
            arglist = sys.argv[1:]
        return plac_call(self.plac_func, arglist=arglist, eager=eager, version=version)

    __call__ = call


class PlacSubCommandUnknownError(Exception):
    pass


class PlacMasterCommand:
    """
    A master command to manage subcommands
    """
    def __init__(self, name: str, *commands, desc: str=None, default: str=None):
        assert all((isinstance(c, PlacCommand) for c in commands)), 'command must be a PlacCommand instance'
        self.commands = {c.name: c for c in commands}
        self.name = name
        self.default = default
        self.desc = desc or f'this is `{name}` master program.' 

    def __missing__(self, name: str):
        cmds = ', '.join(self.commands)
        return f'command "{name}" is not valid. List of available commands: {cmds}'

    def help(self, arglist=None, eager=True, version=None):
        cmds = self.commands
        if 'help' in cmds:
            return cmds['help'](arglist=arglist, eager=eager, version=version)
        else:
            s = [self.desc, '', 'available commands:']
            for name, c in cmds.items():
                _ = f'{name} '
                s.append(f'   {_:.<30s} {c.desc}')
            s.append('')
            s.append(f'To get specific help of particular subcommand, just type: `{self.name} help {{subcommand}}`')
            print('\n'.join(s))

    def help_subcommand(self, cmd: str, eager=True, version=None):
        return self.commands[cmd](arglist=['-h'], eager=eager, version=version)

    def run_subcommand(self, cmd: str, **kwargs):
        try:
            return self.commands[cmd](**kwargs)
        except KeyError:
            raise PlacSubCommandUnknownError(self.__missing__(cmd))

    def run_default(self, **kw):
        if self.default is None:
            return self.help(**kw)
        else:
            return self.commands[self.default](**kw)

    def call(self, arglist=None, eager=True, version=None):
        if arglist is None:
            arglist = sys.argv[1:]
        if len(arglist) == 0:
            return self.run_default(arglist=[], eager=eager, version=version)
        elif len(arglist) == 1:
            c = arglist[0]
            if c in ('-h', '--help', 'help'):
                return self.help(arglist=[])
            else:
                return self.run_subcommand(c, arglist=[], eager=eager, version=version)
        else:
            c0 = arglist[0]
            if c0 == 'help':
                return self.help_subcommand(arglist[1], eager=eager, version=version)
            else:
                return self.run_subcommand(c0, arglist=arglist[1:], eager=eager, version=version)

    __call__ = call
