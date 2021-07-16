# coding: utf-8

"""
(de-)Serialization tools
"""

import importlib
import pickle


class PickleProtocol:
    def __init__(self, level: int):
        self.previous = pickle.HIGHEST_PROTOCOL
        self.level = level or self.previous

    def __enter__(self):
        importlib.reload(pickle)
        pickle.HIGHEST_PROTOCOL = self.level

    def __exit__(self, *exc):
        importlib.reload(pickle)
        pickle.HIGHEST_PROTOCOL = self.previous


def pickle_protocol(level):
    """
    Context manager allowing to select specific pickling protocol

    Usage:
        >>> with pickle_protocol(4):
        >>>     do_stuff()
    """
    return PickleProtocol(level)


def safer_eval(e: str, env: dict=None):
    """Evaluate given string expression, but in a more restricted context: no builtins,
    no access to private methods / attributes and names.
    
    WARNING: this is not safe, and could pose a threat if the expression contains malicious code!
    Use only on trusted / safe data
    """
    if '__' in e:
        raise ValueError('`__` are not allowed in expression')
    if '._' in e:
        raise ValueError('access to private attribute / methods (`._`) is not allowed in expression')
    g = {'__builtins__': {}}
    return eval(e, g, env)
