#!/usr/bin/env python3
# coding: utf-8

"""

"""

import collections


class KeyNotFound:
    pass


class NoDefault:
    pass


class CallIfDefault:
    def __init__(self, func: callable, *args, **kw):
        self.func = func
        self.args = args
        self.kw = kw

    def __call__(self):
        return self.func(*self.args, **self.kw)


def dict_default(x, key=None):
    """Return x if x is not an instance of `CallIfDefault` else execute the code in `CallIfDefault`"""
    if isinstance(x, NoDefault):
        if key is None:
            raise KeyError()
        else:
            raise KeyError(key)
    elif isinstance(x, CallIfDefault):
        return x()
    else:
        return x


def dict_deep_update(d, u, handlers=None):
    """
    Deep update a dictionary using another. Any value of type other than that of a mapping will be replaced by new value
    unless a specific handler function has be given for that type

    Args:
        d (dict): original dict
        u (dict): update dict
        handlers (dict): functions (values) to handle a specific type (keys) update
            eg. `{list: operator.add}`

    Returns:
        d (dict): modified dict
    """
    if handlers is None:
        handlers = {}
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = dict_deep_update(d.get(k, {}), v, handlers)
            d[k] = r
        elif k in d:
            h = handlers.get(type(v), None)
            if h is not None:
                d[k] = h(d[k], u[k])
            else:
                d[k] = u[k]
        else:
            d[k] = u[k]
    return d


def dict_get_first_of(d: dict, key, *opt_keys, return_key: bool = False, **kw):
    """Return the first value for which the key is in the dict"""
    knf = KeyNotFound()
    k = key
    v = d.get(key, knf)
    n = len(opt_keys)
    i = 0
    while isinstance(v, KeyNotFound) and i < n:
        k = opt_keys[i]
        v = d.get(k, knf)
        i += 1

    if isinstance(v, KeyNotFound):
        if 'default' in kw:
            _def = dict_default(kw['default'])
            if return_key:
                return None, _def
            else:
                return _def
        else:
            raise KeyError('none of the provided keys found in the dict')
    if return_key:
        return k, v
    else:
        return v


def dict_deep_get(d: dict, key0, *keys, **kw):
    knf = KeyNotFound()
    v = d.get(key0, knf)
    path = [key0]
    for k in keys:
        if not isinstance(v, dict):
            if isinstance(v, KeyNotFound):
                break
            raise TypeError(f'value under dict path "{" -> ".join(path)}" is not a dict')
        v = v.get(k, knf)
        path.append(k)
    if isinstance(v, KeyNotFound):
        if 'default' in kw:
            v = dict_default(kw['default'])
        else:
            raise KeyError(f'keys path "{" -> ".join(path)}" not valid')
    return v
