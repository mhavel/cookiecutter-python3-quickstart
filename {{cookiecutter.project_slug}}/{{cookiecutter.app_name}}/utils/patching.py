# coding: utf-8

import types


def instancemethod(func, obj, cls=None):
    """attach a function to an instance of a class: useful for dynamic method creation
    (eg. from an expression string)"""
    return types.MethodType(func, obj)


def attach_method(name, func, obj):
    method = instancemethod(func, obj)
    setattr(obj, name, method)
    return obj
