#!/usr/bin/env python3
# coding: utf-8

"""
Tools to work with Path str / instances.
"""

import os
from pathlib import Path
import logging
import shutil
from hashlib import sha1
import uuid
import re
from fnmatch import fnmatch
import operator
from functools import reduce


PTYPE = getattr(re, 'Pattern', getattr(re, '_pattern_type', None))  # Py 3.7 introduced the 'Pattern' type
if PTYPE is None:
    # last resort: if above piece of code failed, just extract the type from an actual compiled regexp
    PTYPE = type(re.compile(r'a'))


def exists_and_newer(p1: Path, p2: Path, *others, op_paths=operator.or_, details: bool=True):
    res = [False, False]
    if p1.is_file():
        t1 = p1.stat().st_mtime
        res[0] = True
        res1 = []
        for p in ((p2, ) + others):
            if not p.is_file():
                res1.append(False)
            elif t1 < p.stat().st_mtime:
                res1.append(False)
            else:
                res1.append(True)
        res[1] = reduce(op_paths, res1[1:], res1[0])
    if not details:
        res = operator.and_(*res)
    return res


def absolute_path(path: Path, root: Path=None):
    p = path.expanduser()
    if root is None:
        p = p.resolve()
    elif not p.is_absolute():
        p = root / p
    return p
    
    
def rooted_path(path: Path, root: Path, base: Path = None):
    if root is None:
        if base is None:
            return path
        else:
            return base / path.name
    if base is None:
        base = Path.cwd()
    return base / path.relative_to(root)


def relative_to(path: Path, rel: Path = None):
    if rel is None:
        rel = Path.cwd()

    try:
        return path.expanduser().resolve().relative_to(rel.expanduser().resolve())
    except ValueError:
        return path


def relative_path(p1, p2=None):
    """return path `p1` relative to `p2`, if if that means starting from /"""
    if p2 is None:
        p2 = Path.cwd()
    else:
        p2 = p2.expanduser().resolve()
    p1 = p1.expanduser().resolve()
    try:
        rel = p1.relative_to(p2)
    except ValueError:
        # find it the hard way
        pp1 = p1.parts
        pp2 = p2.parts
        i = 0
        while pp1[i] == pp2[i]:
            i += 1
        pp1 = p1.parts[i:]
        pp2 = p2.parts[i:]
        up = '../' * len(pp2)
        down = '/'.join(pp1)
        rel = Path(f'{up}{down}')
    return rel


def filter_paths(paths, pattern: str = None, regex: (str, PTYPE) = None, files=True, directories=True,
                 case_sensitive=False, on_names=True, exclude=False):
    """filter a sequence of paths according to the given parameters. Case-insensitive"""
    if not files:
        paths = (x for x in paths if not x.is_file())
    if not directories:
        paths = (x for x in paths if not x.is_dir())
    if on_names:
        def iterator(seq):
            return ((x, x.name) for x in seq)
    else:
        def iterator(seq):
            return ((x, str(x)) for x in seq)
    if exclude:
        op = operator.not_
    else:
        op = operator.truth
    if pattern is not None:
        if case_sensitive:
            pat = pattern.lower()
            paths = (x for x, _ in iterator(paths) if op(fnmatch(_.lower(), pat)))
        else:
            paths = (x for x, _ in iterator(paths) if op(fnmatch(_, pattern)))
    elif regex is not None:
        if isinstance(regex, str):
            if case_sensitive:
                regex = re.compile(regex, re.I)
            else:
                regex = re.compile(regex)
        else:
            assert isinstance(regex, PTYPE), '`regex` must be a string or a compiled re pattern'
        paths = (x for x, _ in iterator(paths) if regex.match(_))
    return paths


def riglob(path: Path, pattern: str = None, regex: (str, PTYPE) = None, files=True, directories=True):
    """same as Path.rglob method, but instead match on given pattern or regex, case-insensitively, and filtering on
    path type (file and / or directory
    If a compiled regex is provided, the case-sensitivity depends on it.
    """
    return filter_paths(path.rglob('*'), pattern=pattern, regex=regex, files=files, directories=directories)


def iglob(path: Path, pattern: str = None, regex: (str, PTYPE) = None, files=True, directories=True):
    """same as Path.glob method, but instead match on given pattern or regex, case-insensitively, and filtering on
    path type (file and / or directory)
    If a compiled regex is provided, the case-sensitivity depends on it.
    """
    return filter_paths(path.glob('*'), pattern=pattern, regex=regex, files=files, directories=directories)


def ensure_file(path, name=None, ext=None, mkdir=False, absolute=True):
    """built a file path, with optional guarantee on its extension, parent directory existence, and eventually name
    return an absolute path by default
    """
    if ext is not None:
        if not ext.startswith('.'):
            ext = f'.{ext}'

    if path is None:
        assert name is not None, 'you must provide a path and / or a name'
        p = Path(name).expanduser()
        p_need_ext = not p.name.lower().endswith(ext.lower()) if ext is not None else False
    else:
        p = Path(path).expanduser()
        p_need_ext = not p.name.lower().endswith(ext) if ext is not None else False

        # make sure it has proper name
        if name is not None:
            n_need_ext = not name.lower().endswith(ext.lower()) if ext is not None else False
            if n_need_ext:
                name += ext

            if p.is_dir():
                p /= name
            elif p.is_file():
                p = p.with_name(name)
            elif p_need_ext:
                # does not exist and missing extension -> consider as a folder
                p /= name
            else:
                # doest not exist and not missing extension -> replace the name
                p = p.with_name(name)
            p_need_ext = False

    # make sure it has proper extension
    if p_need_ext:
        p = p.with_name(p.name + ext)

    if p.is_file():
        # it is an existing file
        pass
    elif p.is_dir():
        # error: it is an existing directory
        raise ValueError(f'{p} is an existing directory: cannot ensure path as a file')
    elif not p.parent.is_dir() and mkdir:
        # does not exist: make sure the parent directory exists
        p.parent.mkdir(parents=True)

    if absolute:
        return p.resolve()
    else:
        return p


def copy(path, new_path):
    ps = Path(path).expanduser()
    pt = Path(new_path).expanduser()
    if ps.is_file():
        return shutil.copy2(ps.as_posix(), pt.as_posix())
    else:
        return shutil.copytree(ps.as_posix(), pt.as_posix())


copy_to = copy


def merge(path, new_path, copy=True, deep=True):
    """merge two folders"""
    s = Path(path).expanduser().resolve()
    assert s.is_dir(), '`path` (source) must be an existing directory'
    t = Path(new_path).expanduser().resolve()
    if not t.exists():
        if not copy:
            s.rename(t)
        else:
            copy_to(s, t)
    else:
        assert t.is_dir(), '`new_path` (target) must either be a directory or not exist'
        s_files = s.glob('*')
        t_files = t.glob('*')
        t_names = [_.name for _ in t_files]
        for fs in s_files:
            ft = t / fs.name
            if fs.name not in t_names:
                if not copy:
                    fs.rename(ft)
                else:
                    copy_to(fs, ft)
            if not deep:
                rm(ft, requires_empty=False)
                fs.rename(ft)
            elif fs.is_file():
                ft.unlink()
                fs.rename(ft)
            else:
                merge(fs, ft, copy=copy, deep=deep)
    return


def backup(path, ext='.backup', versioned_format='{ext}.v{i}', method='copy'):
    """backup a file / folder"""
    p = Path(path).expanduser().resolve()
    name = p.name + ext
    b = p.with_name(name)
    i = 0
    is_file = p.is_file()
    _copy = True
    _symlink = ''
    _all_symlinks = True
    ho = None
    while b.exists():
        if is_file and not _symlink:
            if ho is None:
                ho = sha1(p.read_bytes()).hexdigest()
            hb = sha1(b.read_bytes()).hexdigest()
            if ho == hb:
                _copy = False
                _symlink = b
        elif _symlink and _all_symlinks:
            _all_symlinks = _all_symlinks and b.is_symlink()
        i += 1
        name = p.name + versioned_format.format(ext=ext, i=i)
        b = p.with_name(name)
    if _copy:
        # make a backup
        if method == 'copy':
            # copy
            copy_to(p, b)
        elif method == 'rename':
            # rename = move
            p.rename(b)
        else:
            raise ValueError(f'unknown backup method "{method}": must be "copy" or "rename"')
    else:
        # valid backup found -> symlink incremented version to previous valid backup
        # allows for clear view of latest backup, while not eating up disk space for nothing
        if _symlink:
            if not _all_symlinks:
                # not created if latest non-symlink backup is our intended backup
                b = _symlink
            else:
                b.symlink_to(_symlink, target_is_directory=p.is_dir())
        if method == 'rename':
            # backup already exist, but 'rename' ask, so remove the original file / folder
            rm(p, requires_empty=False)
    return b


def rmdir(path, requires_empty=True):
    p = Path(path).expanduser().resolve()
    assert p.is_dir(), '`path` must exists to be removed'
    assert p != Path.cwd(), 'you cannot remove the current working directory ; change directory first'
    if requires_empty:
        p.rmdir()
    else:
        shutil.rmtree(str(p))


def rm(path, requires_empty=True):
    p = Path(path).expanduser().resolve()
    if p.is_file():
        p.unlink()
    else:
        rmdir(path, requires_empty=requires_empty)


class ChdirContext:
    """
    A class to ease change of directory between 2 folders, with the possibility to change to other path as well,
    rename, ...
    """
    def __init__(self, new_dir=None):
        self.start = Path.cwd()
        if new_dir is None:
            self.new_dir = None
        else:
            p = Path(new_dir).expanduser().resolve()
            if not p.exists():
                p.mkdir(parents=True)
            else:
                assert p.is_dir(), '`new_dir` cannot be a file'
            self.new_dir = p
        self._in_new = False
        self._temp_dirs = []

    @staticmethod
    def relative_path(path):
        """return given path relative to current path (in relative form, eg. '../file.csv')"""
        return relative_path(path)

    def relative_new_path(self, path=None):
        """return given path (or current one) relative to `new_dir` path (in relative form, eg. '../file.csv')"""
        if path is None:
            path = Path.cwd()
        return relative_path(path, self.new_dir or self.start)

    def relative_start_path(self, path=None):
        """return given path (or current one) relative to `start` path (in relative form, eg. '../file.csv')"""
        if path is None:
            path = Path.cwd()
        return relative_path(path, self.start)

    def chdir_new(self):
        """change current directory to `new_dir` directory"""
        if self.new_dir is not None:
            os.chdir(str(self.new_dir))
            self._in_new = True

    def chdir_start(self):
        """change current directory to `start` directory"""
        os.chdir(str(self.start))
        self._in_new = False

    @staticmethod
    def backup(path, ext='.backup', versioned_format='{ext}.v{i}', method='copy'):
        return backup(path, ext, versioned_format, method)

    def mkdir_temp(self, basename='', chdir=False):
        """create a temporary folder under current directory"""
        p = Path.cwd()
        if basename:
            name = f'{basename}--'
        else:
            name = ''
        t = f'{name}{uuid.uuid4()}'
        while (p / t).is_dir():
            t = f'{name}{uuid.uuid4()}'
        p /= t
        p.mkdir()
        self._temp_dirs.append(p)
        if chdir:
            os.chdir(str(p))
        return p

    def rm_temp_dirs(self, requires_empty=True):
        """remove all temporary folders created with this instance using `mkdir_temp` method"""
        left = []
        for p in self._temp_dirs:
            if not p.exists():
                # already removed
                continue
            try:
                if requires_empty:
                    p.rmdir()
                else:
                    shutil.rmtree(str(p))
            except Exception as err:
                logging.error(f'cannot delete directory "{p}" ; error is: {err}')
                left.append(p)
        self._temp_dirs = left

    @staticmethod
    def rmdir(path, requires_empty=True):
        return rmdir(path, requires_empty)

    @staticmethod
    def rm(path, requires_empty=True):
        return rm(path, requires_empty)

    def chdir(self, path=None):
        """change current working directory (default: switching between `new_dir` and `start` directories)"""
        if path is not None:
            os.chdir(path)
            self._in_new = False
        elif self._in_new:
            os.chdir(str(self.start))
            self._in_new = False
        elif self.new_dir is not None:
            os.chdir(str(self.new_dir))
            self._in_new = True

    @staticmethod
    def _rename_dir(new_path, old_path=None):
        p = Path(new_path).expanduser().resolve()
        assert not p.exists(), '`new_path` must not exist to rename current path'
        # change to parent directory before renaming current
        cwd = Path.cwd()
        if old_path is None:
            o = cwd
            a = p
        else:
            o = Path(old_path).expanduser().resolve()
            assert o.is_dir(), '`old_path` must be an existing directory'
            if o != cwd:
                a = cwd
            else:
                a = p
        os.chdir(str(o.parent))
        o.rename(p)
        os.chdir(str(a))
        return p

    def rename_dir(self, new_path):
        """rename current path"""
        c = Path.cwd()
        if c == self.start:
            p = self.rename_start(new_path)
        elif c == self.new_dir:
            p = self.rename_new(new_path)
        else:
            p = self._rename_dir(new_path)
        return p

    def rename_start(self, new_path):
        p = self._rename_dir(new_path, self.start)
        self.start = p
        return p

    def rename_new(self, new_path):
        if self.new_dir is not None:
            p = self._rename_dir(new_path, self.new_dir)
            self.new_dir = p
            return p

    def glob(self, pattern: str):
        """return files iterator matching pattern in current directory"""
        return Path.cwd().glob(pattern)

    def rglob(self, pattern: str):
        """return recursive files iterator matching pattern in current directory"""
        return Path.cwd().rglob(pattern)

    def __enter__(self):
        if self.new_dir is not None:
            os.chdir(str(self.new_dir))
            self._in_new = True
        return self

    def __exit__(self, et, ev, tb):
        os.chdir(str(self.start))
        self._in_new = False


def with_name(path: Path, name: str, keep_extension: bool = True, ditch_extension: bool = False, ext: (int, str) = None):
    if ext is not None:
        if isinstance(ext, int):
            ext = ''.join(path.suffixes[-ext:])
    else:
        ext = path.suffix
    e = ext.lower()
    if not keep_extension:
        if ditch_extension and name.lower().endswith(e):
            name = name[:-len(e)]
    elif not name.lower().endswith(e):
        name += ext
    return path.with_name(name)


def safe_rename(path: (str, Path), name: (str, Path), keep_extension: bool = True, ditch_extension: bool = False,
                ext: (int, str) = None, backup_ext: str = '.backup', versioned_format: str = '{backup_ext}.v{i}',
                method: str = 'backup'):
    """safely rename (move) a file / folder from one path to another, optionally backing-up existing destination.

    Args:
        path (str|Path): the source path
        name (str|Path): the new name or path ; if a string with not '/', will keep source's parent path, use './'
            prefix to move it to current working directory
        keep_extension (bool=True): keep source's extension if `path` is a file
        ditch_extension (bool=False): remove source's extension if `path` is a file
        ext (int|str=None): extension to enforce on new path ; if an int, use to gather source's extension from
            `path.suffixes[-ext:]` ; if a string, use a given
        backup_ext (str='.backup'): the extension for backup file
        versioned_format (str='{backup_ext}.v{i}'): the extension pattern for backup file, if backup name already taken
        method (str='backup'): the backup method ; one of:
            'backup' = move the existing destination to `{dest}.backup`
            'replace' = remove existing destination and replace with source
            'merge' = merge source and existing destination (deep)
            'raise' = raise an error if destination exists
            'skip' = does not rename if destination exists
    """
    s = Path(path).expanduser().resolve()
    assert s.exists(), f'{path} does not exist'
    if isinstance(name, str) and '/' not in name and name not in ('.', '/'):
        t = s.with_name(name)
    else:
        t = Path(name).expanduser().resolve()
    if s.is_file():
        t = with_name(t.with_name(s.name), t.name, keep_extension=keep_extension, ditch_extension=ditch_extension,
                      ext=ext)
    if t.exists():
        if method == 'backup':
            backup(t, backup_ext, versioned_format.replace('{backup_ext}', '{ext}'), method='rename')
        elif method == 'replace':
            rm(t, requires_empty=False)
        elif method == 'merge':
            # special case: if source is a folder, move in target its content (overwriting existing files) ; if its a
            # file, replace it
            if s.is_file():
                t.unlink()
            else:
                merge(s, t, copy=False, deep=True)
                return t
        elif method == 'raise':
            raise ValueError(f'destination path already exists and `method="raise"`')
        elif method == 'skip':
            return
    if not t.parent.exists():
        t.parent.mkdir(parents=True)
    s.rename(t)
    return t
