# coding: utf-8

"""
(de-)Serialization tools
"""

import importlib
import pickle


class PickleProtocol:
    def __init__(self, level):
        self.previous = pickle.HIGHEST_PROTOCOL
        self.level = level

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
