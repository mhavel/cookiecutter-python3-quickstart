#!/usr/bin/env python3
# coding: utf-8

"""
some decorators
"""

from pathlib import Path
from functools import wraps
import inspect
import json


def as_list(x):
    if isinstance(x, str):
        x = [x]
    elif hasattr(x, '__iter__'):
        x = list(x)
    else:
        x = [x]
    return x


class Defaults:
    """
    Decorator to provide default values to a function.

    Args:
        c (Path, dict, str): the dict of default values ; can be a dict, a Path to a JSON file, a str representing
            a JSON file path, or a str to be parsed as JSON data ; read only at compilation time.
        _raise_for_missing_file (bool = False): if True, raise a FileNotFoundError if the given JSON file cannot be read
        _json_reader (callable = None): provide a custom JSON file reader

    Notes:
        if `c` is provided, it represent a file path, and if it does not exits, the defaults will be set as {},
        without any warning.

        The estimated performance impact on a single CPU for a function is about 1µs (overhead for args processing).

    Example:
        >>> @Defaults(dict(x=1.45, args=(5, 6, 7)))
        >>> def my_function(x, y=1, z=True, *args, a=None, b='abcd'):
        >>>     print(x, y, z)
        >>>     print(args)
        >>>     print(a, b)
        >>> my_function()
        1.45, 1, True
        (5, 6, 7)
        None, 'abcd'

        This example is a bit silly, but this decorator is very useful when used with files: the user can control
        the default behavior of a function using its own JSON file, without having to dig into the code or
        create another mechanism to handle its preferred defaults
    """
    def __init__(self, c: (Path, dict, str), _raise_for_missing_file=False, _json_reader=None):
        """
        Decorator to provide default values to a function.

        Args:
            c (Path, dict, str): the dict of default values ; can be a dict, a Path to a JSON file, a str representing
                a JSON file path, or a str to be parsed as JSON data
            _raise_for_missing_file (bool = False): if True, raise a FileNotFoundError if the given JSON file cannot be
                read
            _json_reader (callable = None): provide a custom JSON file reader

        Notes:
            if `c` is provided, it represent a file path, and if it does not exits, the defaults will be set as {},
            without any warning.

        Example:
            >>> @defaults(dict(x=1.45, args=(5, 6, 7)))
            >>> def my_function(x, y=1, z=True, *args, a=None, b='abcd'):
            >>>     print(x, y, z)
            >>>     print(args)
            >>>     print(a, b)
            >>> my_function()
            1.45, 1, True
            (5, 6, 7)
            None, 'abcd'

            This example is a bit silly, but this decorator is very useful when used with files: the user can control
            the default behavior of a function using its own JSON file, without having to dig into the code or
            create another mechanism to handle its preferred defaults
        """
        # default attribute: with no file, hence not specific wrapper (except with annotations for `plac`
        self.wrapper = None
        self.config = None
        self.inspection = dict(
            x_poskw=[],
            def_args=[],
            def_kwargs={},
            def_kw={},
            def_poskw={},
            n_poskw=0,
            has_args=False,
            has_kwargs=False,
        )

        self.func = None

        # config
        if not c:
            return
        if isinstance(c, dict):
            config = c.copy()
        elif isinstance(c, str):
            config = self.config_from_string(c, _json_reader, _raise_for_missing_file)
        elif isinstance(c, Path):
            config = self.config_from_path(c, _json_reader, _raise_for_missing_file)
        else:
            assert isinstance(c, (tuple, list)), '`c` must be a dict, str or Path instance (or a seq of str or Path)'
            config = None
            for _c in c:
                _conf = None
                if isinstance(_c, str):
                    _conf = self.config_from_string(_c, _json_reader, _raise_for_missing_file)
                elif isinstance(_c, Path):
                    _conf = self.config_from_path(_c, _json_reader, _raise_for_missing_file)
                if _conf is not None:
                    config = _conf
                    break
        self.config = config

    @classmethod
    def config_from_string(cls, s: str, reader=None, missing_raises_error=False, **kw):
        s = s.format(**kw)
        if s[-5:].lower().endswith('.json'):
            config = cls.read_config(Path(s), reader, missing_raises_error)
        else:
            config = json.loads(s)
        return config

    @classmethod
    def config_from_path(cls, p: Path, reader=None, missing_raises_error=False):
        assert p.suffix.lower() == '.json', '`c` as path must be a JSON file with a ".json" extension'
        return cls.read_config(p, reader, missing_raises_error)

    @staticmethod
    def read_config(path: Path, reader=None, missing_raises_error=False):
        p = path.expanduser().resolve()
        if p.is_file():
            if callable(reader):
                config = reader(p)
            else:
                config = json.loads(p.read_text())
        elif missing_raises_error:
            raise FileNotFoundError(f'{p} is not a readable file')
        else:
            config = None
        return config

    def __call__(self, func):
        self.func = func

        # no config at all ==> minimal / no wrapping
        if self.config is None:
            # no wrapping done at all
            self.wrapper = func
            return func

        self.inspect_func(func)
        insp = self.inspection

        @wraps(func)
        def wrapper(*args, **kwargs):
            na = len(args)      # number of positional arguments provided by user

            # build kwargs: init with defaults from config
            if insp['has_kwargs']:
                kw = dict(insp['def_kwargs'], _defaults_triggered=True, **insp['def_kw'])
            else:
                kw = dict(insp['def_kw'])
            # add user provided kwargs (even for variables that could be positional too)
            kw.update(kwargs)

            # build args: use defaults from config and any 'positional or keyword' provided by user in kwargs
            _args = [kw.pop(_, insp['def_poskw'][_]) for _ in insp['x_poskw'][na:]]

            # *a = *args + _args
            a = list(args) + _args

            # could extend with defaults *args in config if room for it and not provided by user
            if na <= insp['n_poskw'] and insp['has_args']:
                a.extend(insp['def_args'])
            return func(*a, **kw)

        wrapper.defaults = {'*args': insp['def_args'], '**kwargs': insp['def_kwargs'],
                            'keywords': insp['def_kw'], 'pos_kw': insp['def_poskw']}
        wrapper._meta = insp

        self.wrapper = wrapper
        return wrapper

    def inspect_func(self, func):
        config = self.config

        sig = inspect.signature(func)
        x_poskw = []
        x_kw = []
        x_ = []
        has_args = has_kwargs = False
        for p in sig.parameters.values():
            k = p.kind
            x = p.name
            x_.append(x)
            if k == p.POSITIONAL_ONLY:
                # x_pos.append(x)
                # Python has no syntax to support positional-only params (only some C extension eg.)
                pass
            elif k == p.POSITIONAL_OR_KEYWORD:
                x_poskw.append(x)
            elif k == p.KEYWORD_ONLY:
                x_kw.append(x)
            elif k == p.VAR_POSITIONAL:
                has_args = True
            elif k == p.VAR_KEYWORD:
                has_kwargs = True
        # def_pos = as_list(config.pop('positional', []))
        def_args = as_list(config.pop('args', []))
        def_kwargs = config.pop('kwargs', {})
        def_kwargs.update({k: config.pop(k) for k in list(config) if k not in x_})
        def_kw = {k: v for k, v in config.items() if k in x_kw}
        def_poskw = {k: v for k, v in config.items() if k in x_poskw}
        n_poskw = len(x_poskw)

        self.inspection.update(
            x_poskw=x_poskw,
            def_args=def_args,
            def_kwargs=def_kwargs,
            def_kw=def_kw,
            def_poskw=def_poskw,
            n_poskw=n_poskw,
            has_args=has_args,
            has_kwargs=has_kwargs)
