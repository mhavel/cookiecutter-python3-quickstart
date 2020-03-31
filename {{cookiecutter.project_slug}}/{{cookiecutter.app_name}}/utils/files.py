#!/usr/bin/env python

"""
Some tools to work with files
"""

from pathlib import Path
import hashlib
from functools import partial


def hash_file(path: (str, Path), algo=None, chunk_kb=128) -> str:
    """Compute the hash sum of a file, ready in chunks ; default algorithm is Sha1, and chunk size is 128 kB"""
    path = Path(path).expanduser().resolve()
    assert path.is_file(), f'path {path} is not a file'

    if algo is None:
        algo = hashlib.sha1
    elif isinstance(algo, str):
        algo = getattr(hashlib, algo)
    else:
        assert callable(algo), f'`algo` must be a hashlib algorithm name or a callable'

    # src: https://stackoverflow.com/a/44873382
    b  = bytearray(chunk_kb * 1024)
    mv = memoryview(b)
    with path.open(mode='rb', buffering=0) as f:
        reader = partial(f.readinto, mv)
        h = algo()
        for n in iter(reader, 0):
            h.update(mv[:n])

    return h.hexdigest()
