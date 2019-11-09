#!/usr/bin/env python3
# coding: utf-8

"""
Tools for interactive console prompts
"""

import uuid

from .types import smart_bool


def generic(question, *comments, default_value=None, prefix='> ', suffix='   ', default_string=None, answer_type=None,
            auto_enter=False):
    """a generic prompt"""
    if default_string is None:
        default_string = f'[{str(default_value)}]' if default_value else ''
    da = f' {default_string}' if default_string else ''

    q = prefix + question.strip()
    if not q.endswith('?'):
        q += '?'
    q += da
    for c in comments:
        q += f'\n{prefix}{c}'
    if comments:
        q += f'\n{prefix}'
    else:
        q += suffix
    if not auto_enter:
        a = input(q).strip()
    else:
        print(q)
        return default_value
    if not a:
        return default_value
    elif callable(answer_type):
        return answer_type(a)
    else:
        return a


def yes_no(question, *comments, default_yes=True, **kwargs):
    """Create a prompt with a yes/no (True/False) expected answer"""
    if default_yes:
        default_value = True
        default_string = '[Y/n]'
    else:
        default_value = False
        default_string = '[y/N]'
    return generic(question, *comments, default_value=default_value, default_string=default_string,
                   answer_type=smart_bool, **kwargs)


def uid(question, *comments, default_uid=None, uid_len=8, **kwargs):
    """prompt for unique ID"""
    if default_uid is None:
        default_uid = str(uuid.uuid4())[:uid_len]
    return generic(question, *comments, default_value=default_uid, **kwargs)
