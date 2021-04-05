# coding: utf-8

"""
I/O
"""

from typing import Union
from pathlib import Path


def get_output(name: str, root: Union[str, Path]=None, check_suffix: callable=None, **keywords):
    if isinstance(root, Path):
        root = Path(str(root).format(**keywords)).expanduser()
    elif root is not None:
        root = Path(root.format(**keywords)).expanduser()
    
    if isinstance(name, Path):
        out = Path(str(name).format(**keywords)).expanduser()
    else:
        out = Path(name.format(**keywords)).expanduser()

    if len(out.parts) == 1 and '/' not in name and root is not None:
        out = root / out
    
    if check_suffix is not None:
        return check_suffix(out)
    else:
        return out
