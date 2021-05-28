#!/usr/bin/env python3
# coding: utf-8

"""
Strings tools
"""

from typing import Union
import unicodedata
import re
from string import ascii_lowercase
import hashlib
from fnmatch import fnmatch


PTYPE = getattr(re, 'Pattern', getattr(re, '_pattern_type', None))  # Py 3.7 introduced the 'Pattern' type
if PTYPE is None:
    # last resort: if above piece of code failed, just extract the type from an actual compiled regexp
    PTYPE = type(re.compile(r'a'))


STOPWORDS = ['à', 'de', 'des', 'la', 'le', 'les', 'un', 'une', 'mes', 'ma', 'mon',
             'tes', 'ta', 'ton', 'sa', 'ses', 'son', 'vos', 'nos']
STOPWORDS.extend(ascii_lowercase)


def normalize(*args, remove_accents=True, decapitalize=True, lowercase=False, stopwords=True,
              norm_spaces=True, remove_quotes=True, encoding='utf-8'):
    if remove_accents:
        args = [unicodedata.normalize('NFD', _).encode('ascii', 'ignore').decode(encoding) for _ in args]
    if remove_quotes:
        reg = re.compile(r'[\'",`]')
        args = [reg.subn(' ', _)[0] for _ in args]
    if lowercase:
        decapitalize = False
        args = list(map(str.lower, args))
    if norm_spaces or decapitalize or stopwords:
        w = [_.split() for _ in args]
        if decapitalize:
            w = [[_.lower() if _.istitle() else _ for _ in _w] for _w in w]
        if stopwords:
            if stopwords is True:
                stopwords = STOPWORDS
            else:
                assert isinstance(stopwords, (tuple, list))
            if lowercase:
                w = [[_ for _ in _w if _ not in stopwords] for _w in w]
            else:
                w = [[_ for _ in _w if _.lower() not in stopwords] for _w in w]
        args = [' '.join(_) for _ in w]
    if len(args) == 1:
        return args[0]
    else:
        return args


def u2ascii(s, encoding='utf-8', mapping: dict=None) -> str:
    if mapping is not None:
        s = s.translate(str.maketrans(mapping))
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode(encoding)


def hashsum_str(x: Union[str, bytes], algo=None) -> str:
    """Compute the hash sum of the given string / bytes ; default algorithm is Sha1"""
    if algo is None:
        algo = hashlib.sha1
    elif isinstance(algo, str):
        algo = getattr(hashlib, algo)
    else:
        assert callable(algo), f'`algo` must be a hashlib algorithm name or a callable'

    if isinstance(x, str):
        x = x.encode('utf-8')
    return algo(x).hexdigest()


class Matcher:
    def __init__(self, pattern: Union[str, PTYPE], regex: bool=True, regex_flags=0, fullmatch: bool=False):
        func = None
        if isinstance(pattern, str):
            if regex:
                self.pattern = re.compile(pattern, regex_flags)
            else:
                self.pattern = pattern.lower()
                func = self._fnm_func
        else:
            assert isinstance(pattern, PTYPE)
            self.pattern = pattern
        if func is None:
            if fullmatch:
                func = self._re_full_func
            else:
                func = self._re_part_func
        self.match = func

    def _fnm_func(self, arg: str):
        return fnmatch(arg.lower(), self.pattern)

    def _re_full_func(self, arg: str):
        return self.pattern.match(arg) is not None

    def _re_part_func(self, arg: str):
        return self.pattern.search(arg) is not None

    def match_all(self, *args):
        f = self.match
        return all((f(a) for a in args))
    
    def match_any(self, *args):
        f = self.match
        return any((f(a) for a in args))

    def match_none(self, *args):
        return not self.match_any(*args)

    def match_array(self, *args):
        f = self.match
        return [f(a) for a in args]

    def __call__(self, *args, mode='all'):
        if mode == 'all':
            m = self.match_all(*args)
        elif mode == 'any':
            m = self.match_any(*args)
        elif mode == 'none':
            m = self.match_none(*args)
        return m
