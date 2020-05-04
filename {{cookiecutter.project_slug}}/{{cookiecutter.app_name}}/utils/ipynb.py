#!/usr/bin/env python3
# coding: utf-8

"""
Code snippets taken from the internet, and eventually slightly modified
"""


def is_notebook():
    """
    Returns True if code running in a Jupyter Notebook shell

    source: https://stackoverflow.com/a/39662359
    """
    try:
        ip = get_ipython()
    except NameError:
        return False  # Probably standard Python interpreter


    shell = ip.__class__.__name__
    module = ip.__class__.__module__
    if shell == 'ZMQInteractiveShell':
        return True   # Jupyter notebook or qtconsole
    elif shell == 'TerminalInteractiveShell':
        return False  # Terminal running IPython
    elif module == 'google.colab._shell':
        # https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook#comment93642570_39662359
        return True
    else:
        return False  # Other type (?)


def get_display():
    if is_notebook():
        from IPython import display
    else:
        display = None
    return display
