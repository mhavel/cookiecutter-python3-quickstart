#!/usr/bin/env python3
# coding: utf-8

"""
Tools to deal with configuration files, in the YAML format
"""

from pathlib import Path
import srsly
import yaml

from .data import read_data_file, get_data_file
from ..utils.downloads import download


__all__ = ['read_file', 'config']


# YAML C loader only available when libyaml is installed
YamlLoader = getattr(yaml, 'CLoader', yaml.Loader)


def read_file(path, encoding='utf-8'):
    path = Path(path).expanduser().resolve()
    s = path.suffix.lower()
    if s == '.json':
        return srsly.read_json(path)
    elif s == '.jsonl':
        return srsly.read_jsonl(path)
    elif s in ('.yml', '.yaml'):
        return yaml.load(path.read_bytes(), Loader=YamlLoader)
    elif s in ('.pkl', '.bin', '.pickle'):
        return srsly.pickle_loads(path.read_text(encoding=encoding))
    else:
        return path.read_text(encoding=encoding)


class PkgConfig:
    """
    A class to read the package's configuration file.

    That file can in-turn contains information to locate and eventually read other configuration files.
    These extra config files (and the way to find it) are listed in the package's main configuration file:
        {{ cookiecutter.app_name }}_config.yml

    This file may not exist.
    """
    def __init__(self, path=None):
        if path is None:
            path = Path.cwd() / '{{cookiecutter.app_name}}_config.yml'
            if path.is_file():
                self.path = self._get_path(path)
            else:
                self.path = get_data_file('{{cookiecutter.app_name}}_config.yml')
        else:
            self.path = self._get_path(path)

        self.data = None
        self.default_paths = ['.']
        self.default_download_path = '.'
        self.load(on_missing=b'{}')

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.path}")'

    def __str__(self):
        return str(self.data)

    def help_format(self):
        print(
            f'{self.__class__.__name__} is using the YAML formatted file {self.path}.\nThis file has the following'
            ' format for each of its entry (# start comments):\n'
            '```\n'
            'data_key:\n'
            '  is_file: true    # optional ; defaults to false keys are not among {name, paths, url, download_dest}\n'
            '  name: name_of_the_file   # optional\n'
            f'  paths: [".", "/path/to/find/file"]   # optional ; defaults to {self.default_paths}\n'
            f'  url: url_of_the_file_to_download     # optional ; will ignore `paths`\n'
            '  download_dest: path/to/destination/folder/for_downloaded_file   # optional ; '
            f'defaults to {self.default_download_path}\n'
            '```'
        )

    @staticmethod
    def _get_path(path):
        path = Path(path).expanduser().resolve()
        assert path.is_file(), f'{path} is not readable or does not exists'
        assert path.suffix.lower() in ('.yml', '.yaml'), f'{path} is not a YAML file (extension must be .yml or .yaml)'
        return path

    def add_default_location(self, path: (str, Path), prepend=False):
        if prepend:
            self.default_paths.insert(0, path)
        else:
            self.default_paths.append(path)

    def set_default_download_location(self, path: (str, Path)):
        self.default_download_path = path

    def load(self, path=None, update=False, on_missing=None):
        if path is None:
            if self.data is not None:
                return
            path = self.path
        else:
            path = self._get_path(path)
        data = yaml.load(read_data_file(path, as_bytes=True, on_missing=on_missing), Loader=YamlLoader)
        if self.data is None:
            self.data = data
        elif update:
            self.data.update(data)
        else:
            self.data = data
        self.path = path

    def update(self, **kwargs):
        self.data.update(kwargs)

    def is_file(self, name):
        x = self.data[name]
        is_file = x.get('is_file', None)
        if is_file is None:
            if set(x).difference({'name', 'url', 'paths', '_path', 'is_file', 'download_dest'}):
                x['is_file'] = is_file = False
            else:
                x['is_file'] = is_file = True
        return is_file

    def get_path(self, name, try_default_paths=False, dest_path=None):
        assert self.is_file(name), f'"{name}" entry is not describing a file: cannot get the path'
        x = self.data[name]

        if '_path' not in x:
            fname = x.get('name', name)
            if x.get('url', None) is not None:
                download_dest = x.get('download_dest', self.default_download_path)
                path = download(x['url'], download_dest, fname)
                x['_path'] = path
            else:
                path = None
                if 'paths' in x:
                    p = x['paths']
                    if try_default_paths:
                        p += self.default_paths
                else:
                    p = x.get('paths', self.default_paths)
                tried = set()
                for _p in map(lambda _: Path(_).expanduser().resolve() / fname, p):
                    if _p.parent in tried:
                        continue
                    if _p.exists():
                        x['_path'] = path = _p
                        break
                    tried.add(_p.parent)
                if path is None:
                    if dest_path is None:
                        raise FileNotFoundError(f'`{fname}` (key = {name}) data could not be found in {p}')
                    else:
                        if dest_path is True:
                            dest_path = p[0]
                        path = Path(dest_path).expanduser().resolve() / fname
            return path
        else:
            return x['_path']

    def get(self, name, try_default_paths=False, dest_path=None):
        if self.is_file(name):
            return self.get_path(name, try_default_paths=try_default_paths, dest_path=dest_path)
        # else return the data of that key, whatever it is
        return self.data[name]

    def read(self, name, try_default_paths=False, encoding='utf-8'):
        path = self.get_path(name, try_default_paths=try_default_paths)
        return read_file(path, encoding=encoding)


config = PkgConfig()
# config.data.setdefault('stopwords', {'_path': get_resource('pkg/data/stopwords.yml')})  # an example to include package's file within the configuration if needed


def get(name, try_default_paths=False, dest_path=None):
    return config.get(name, try_default_paths=try_default_paths, dest_path=dest_path)


def get_path(name, try_default_paths=False, dest_path=None):
    return config.get_path(name, try_default_paths=try_default_paths, dest_path=dest_path)


def read(name, try_default_paths=False, encoding='utf-8'):
    return config.read(name, try_default_paths=try_default_paths, encoding=encoding)
