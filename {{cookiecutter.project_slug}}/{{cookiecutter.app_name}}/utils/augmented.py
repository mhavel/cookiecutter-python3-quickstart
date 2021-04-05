#!/usr/bin/env python3
# coding: utf-8

"""
Augmented Python base-class, and utils
"""

from copy import deepcopy

from .mapping import dict_deep_update, dict_default, dict_get_first_of, KeyNotFound


# ============
#  Dictionary
# ============
_AUGMENTED_DICT_SUPER_METHODS = {
    '__call__', '__dir__', '__repr__', 'get_from_path', 'set_from_path', 'get_first_of',
    'get_first_of_path', 'deep_update', 'pop_from_path', '__setstate__', '__getstate__',
    'from_object', 'from_mapping', 'from_sequence', 'deep_get', 'deepcopy'
}
_AUGMENTED_DICT_OBJECT_METHODS = {

}


class AugmentedDict(dict):
    """
    An augmented Dict class that allows:
        - easy access to nested dict using a string path (and a separator, '.' by default)
        - access (set/get) to values as attribute
        - deep update
        - pickling
        - copy constructors from objects, mappings, sequences

    Inspired partly from: http://code.activestate.com/recipes/577887-a-simple-namespace-class/

    Examples:
            >>> d = AugmentedDict({'a': {'b': 2}, 3: {4: 'here'}})
            >>> d('a', 'b')
            2
            >>> d['a.b']
            2
            >>> d['a'].b
            2
            >>> d.a.b
            2
            >>> d[('a', 'b')]
            2
            >>> d(3, 4)
            'here'
            >>> d[(3, 4)]
            'here'
            >>> d('a', 'c')
            None
            >>> d['a.c']
            Traceback (most recent call last):
                ...
            KeyError: 'key path `a -> c`'
            >>> d('a', 'c', raise_error=True)
            Traceback (most recent call last):
                ...
            KeyError: 'key path `a -> c`'
            >>> d('a', 'b', 'c')
            Traceback (most recent call last):
                ...
            TypeError: argument of type 'int' is not iterable
            >>> d('c', 'a')
            None
    """
    def __call__(self, *args, **kwargs):
        """
        Resolve a possibly deep key

        Args:
            *args: keys path leading to the value to be retrieved
            **kwargs: options

        Keyword Args:
            default: default returned value if the key does not exist (default: None)
            raise_error: if True, raise an error if a key does not exist (default: False)
            pop: if True, remove the key if it does exist (default: False)

        Returns:
            retrieved value
        """
        if not args:
            return self

        _v = self
        default = kwargs.pop('default', None)
        raise_err = kwargs.pop('raise_error', False)
        pop = kwargs.pop('pop', False)

        _p = _v
        k = args[0]
        path = []
        for k in args:
            path.append(k)
            if k in _v:
                _p = _v
                _v = _v[k]
            elif not raise_err:
                return dict_default(default, key=f'key path `{" -> ".join(path)}`')
            else:
                raise KeyError(f'key path `{" -> ".join(path)}`')

        if pop:
            _p.pop(k)

        return _v

    deep_get = __call__

    def __getitem__(self, key):
        """ Access dict values by key.

        Args:
            key: key to retrieve
        """
        try:
            value = super().__getitem__(key)
        except KeyError:
            if isinstance(key, str):
                value = super().__getattribute__('get_from_path')(key, raise_error=True)
            elif isinstance(key, (tuple, list)):
                value = self(*key, raise_error=True)
            else:
                raise
        if isinstance(value, dict):
            # For mixed recursive assignment (e.g. `a["b"].c = value` to work
            # as expected, all dict-like values must themselves be _AttrDicts.
            # The "right way" to do this would be to convert to an _AttrDict on
            # assignment, but that requires overriding both __setitem__
            # (straightforward) and __init__ (good luck). An explicit type
            # check is used here instead of EAFP because exceptions would be
            # frequent for hierarchical data with lots of nested dicts.
            self[key] = value = self.__class__(value)
        return value

    def __dir__(self):
        return list(self)

    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, super().__repr__())

    def __getattribute__(self, name):
        if name in _AUGMENTED_DICT_SUPER_METHODS:
            return super().__getattribute__(name)
        elif name in _AUGMENTED_DICT_OBJECT_METHODS:
            return object.__getattribute__(self, name)

        try:
            # priority given to keys in the augmented dict
            return self[name]
        except KeyError:
            # otherwise try accessing the attribute using regular object method
            try:
                return super().__getattribute__(name)
            except AttributeError:
                raise AttributeError(f'"{name}" is not a valid key path / attribute of the {type(self)} instance')

    def __setattr__(self, key, value):
        """ Set dict values as attributes.

        Args:
            key: key to set
            value: new value for key
        """
        if '.' in key:
            super().__getattribute__('set_from_path')(key, value, sep='.')
        else:
            self[key] = value
        return
                               
    def __contains__(self, key):
        if '.' in key:
            try:
                self.get_from_path(key, raise_error=True)
                return True
            except KeyError:
                return False
        else:
            return super().__contains__(key)

    def deepcopy(self):
        return self.__class__(deepcopy(self))

    copy_ = deepcopy

    def get_from_path(self, e, default=None, sep='.', raise_error=False):
        """
        Same as __call__, but one string argument is used to infer the keys path, separated by `sep` (default: .)

        Args:
            e (str): key path string
            default (=None): default value if not found
            sep (str='.'): separator for keys in path
            raise_error (bool=False): if True, raise an error if no value found under given key path

        Returns:
            retrieved value
        """
        assert isinstance(e, str), 'first argument must be a string representing the keys path'
        return self.__call__(*e.split(sep), default=default, raise_error=raise_error)

    get_ = get_from_path

    def set_from_path(self, e, value, sep='.'):
        """
        Set a value under the keys path

        Args:
            e: string keys path
            value: value
            sep: separator for keys (default: .)
        """
        assert isinstance(e, str), 'first argument must be a string representing the keys path'

        _v = self
        keys = e.split(sep)
        p = []
        for k in keys[:-1]:
            p.append(k)
            if k not in _v:
                _v[k] = {}
                _v = _v[k]
            elif not isinstance(_v[k], dict):
                raise ValueError('keys path [%s] exists but is not a dictionary, as required' % sep.join(p))
            else:
                _v = _v[k]

        k = keys[-1]
        _v[k] = value

    set_ = set_from_path

    def get_first_of(self, *args, return_key=False, **kwargs):
        """
        Return the first value for which the key is in the dict

        Args:
            *args: list of possible key (cannot be key paths)
            return_key (bool=False): if True, return the key's path
            **kwargs: options
        """
        return dict_get_first_of(self, *args, return_key=return_key, **kwargs)

    def get_first_of_path(self, *paths, return_key=False, **kwargs):
        """same as `get_first_of` method, but you can provide key paths too"""
        knf = KeyNotFound()

        def _get(_d, _k):
            try:
                return _d[_k]
            except KeyError:
                return knf
        v = knf
        n = len(paths)
        i = 0
        while isinstance(v, KeyNotFound) and i < n:
            k = paths[i]
            v = _get(self, k)
            i += 1

        if isinstance(v, KeyNotFound):
            if 'default' in kwargs:
                _def = dict_default(kwargs['default'])
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

    def deep_update(self, other=None, handlers=None, **kwargs):
        """
        Do a deep update of the dictionary

        Args:
            other (dict): the dict with updated values
            handlers (dict): a dict of functions (values) to handle other type (keys) of values (eg. list, ...)
            **kwargs: alternative dict with updated values (processed after `other`)
        """
        d = self
        if other is not None:
            if hasattr(other, 'items'):
                d = dict_deep_update(d, other, handlers)
            else:
                d = dict_deep_update(d, dict(other), handlers)

        if kwargs:
            d = dict_deep_update(d, kwargs, handlers)

        self.update(d)

    update_ = deep_update

    def pop_from_path(self, e, sep='.', **kwargs):
        """
        Same as `get_from_path`, but remove the key after retrieving its value

        Args:
            e: string keys path
            sep: separator for keys (default: .)
            **kwargs:

        Keyword Args:
            default: default value if not found. If not provided, will raise an error (as with the .pop method of dict)

        Returns:
            retrieved value
        """
        assert isinstance(e, str), 'first argument must be a string representing the keys path'
        o = dict(pop=True)
        if 'default' in kwargs:
            o['default'] = kwargs.pop('default')
        else:
            o['raise_error'] = True
        return self.__call__(*e.split(sep), **o)

    pop_ = pop_from_path

    # ------------------
    # pickling
    def __setstate__(self, state):
        for k, v in state.iteritems():
            self[k] = v

    def __getstate__(self):
        return dict(**self)

    def __reduce__(self):
        return self.__class__, (dict(**self), )

    # ------------------------
    # "copy constructors"
    @classmethod
    def from_object(cls, obj, names=None):
        if names is None:
            names = dir(obj)
        ns = {name: getattr(obj, name) for name in names}
        return cls(ns)

    @classmethod
    def from_mapping(cls, ns, names=None):
        if names:
            ns = {name: ns[name] for name in names}
        return cls(ns)

    @classmethod
    def from_sequence(cls, seq, names=None):
        if names:
            seq = {name: val for name, val in seq if name in names}
        return cls(seq)

