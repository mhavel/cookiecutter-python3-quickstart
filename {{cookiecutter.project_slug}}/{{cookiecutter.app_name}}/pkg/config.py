#!/usr/bin/env python3
# coding: utf-8

"""
Tools to deal with configuration files, in the YAML format
"""

from pathlib import Path
from copy import deepcopy
import operator

from . import params
from .data import get_data_file
from .readers import interpret_file, read_file, read_yaml
from ..utils.downloads import download
from ..utils.mapping import dict_deep_update
from ..utils import json, yaml


__all__ = ['config', 'ConfigValue', 'PkgConfig']


class ConfigFileError(Exception):
    pass


class PkgConfig:
    """
    A class to setup a globally available configuration in the package.

    Discovery and loading process of config files:
        The PkgConfig will look for the following files (in that order):
            - provided user file (when an instance is created)
              in that case, none of the package's config files will be read!!
            - package's **resource** config (within the code tree ; pkg.params.BASE_CONFIG)
              if existing, then use it as a base config
            - package's **data** config (a shared file written during install ; must be YAML file)
              if existing, then use it to update resource's config (if defined), or use as base config
            - package's **user** config (must be YAML file)
              if existing, then use it to update config (deep update)

    That config can in-turn contains information to locate/download and eventually read other configuration files.
    A typical external config file (JSON, YAML, JSONL, .bin, ascii) can be defined as:
    
        config_key:
            is_file: true   # can be omitted as long as you have defined one of {name, paths, url, download_dest} below
            name: 'name or path of the file'
            paths: [".", "/path/to/find/file"]    # roots where to find this file (local only)
            url: url_of_the_file_to_download      # the URL of the remote file
            download_dest: path/to/destination/folder/for_downloaded_file

    The sub-config contained in the such a file can be retrieved by:
        path = config.get_subconfig_path(config_key)
        data = config.read_subconfig(config_key)
        data = config.get(config_key, read_file=True)
    The way these sub-config files are located can be controlled using the following methods:
        - config.add_default_location(path, prepend=False)
        - config.set_default_download_location(path)

    More generally the following methods can be used:
        * config (re)load / expansion
            - reload initial state: config.reload()
            - expand config: config.expand(path)
            - replace config: config.replace(path)  or  config.replace(data=dict_data)

        * items get / set / update
            - get:
                config[config_key]          # does not read sub-config files
                config.get(config_key, read_file=False)
            - set:
                config[config_key] = data   # another entry
                config.set(config_key, value)
            - update:
                config.update(**kw)         # shallow update
                config.deep_update(**kw)    # deep update ; controls how types are handlers with config.deep_update_handlers's dict

        * save
            config.save()  or   config.save(path)        


    It is possible to not have any configuration file.
    """
    main_config_file = params.DEFAULT_CONFIG_FILE

    # -- config loader --
    def __init__(self, path=None, encoding='utf-8'):
        # sub-config files
        self.default_paths = ['.']
        self.default_download_path = '.'
        self._files = {}

        # final config
        self.data = {}

        # user explicitly provided config file
        self.encoding= encoding
        self.path = path

        # first load
        self._load_init(encoding=encoding)

        # status
        self._updated = False

    @staticmethod
    def validate_config_file(path: (str, Path), must_exists: bool=True):
        path = Path(path).expanduser().resolve()
        if not path.is_file() and must_exists:
            raise ConfigFileError(f'{path} is not readable or does not exist')
        if not path.suffix.lower() in ('.yml', '.yaml', '.json'):
            raise ConfigFileError(f'{path} is not a YAML / JSON file (extension must be .yml, .yaml, or .json)')
        return path

    def _load_init(self, encoding='utf-8'):
        data = {}

        # explicitly provided user's config file
        if self.path is not None:
            data = self._read_config_file(self.path, encoding=encoding)
            self.data = data
            return

        # package's resource base config
        if params.BASE_CONFIG is not None:
            dict_deep_update(data, params.BASE_CONFIG)
        
        # package's installed data config
        if params.INSTALL_CONFIG_FILE is not None:
            path = get_data_file(params.INSTALL_CONFIG_FILE)
            if path.is_file():
                dict_deep_update(data, self._read_config_file(path, encoding=encoding))

        # package's default user config
        path = Path(params.DEFAULT_CONFIG_FILE).expanduser().resolve()
        if path.is_file():
            dict_deep_update(data, self._read_config_file(path, encoding=encoding))
        elif params.CREATE_USER_CONFIG_IF_NONE:
            self.validate_config_file(path, must_exists=False)
            self._export(data, path)
            
        self.data = data

    @classmethod
    def _read_config_file(cls, path: (str, Path), encoding='utf-8', validate: bool=True):
        if validate:
            path = cls.validate_config_file(path)
        else:
            path = Path(path).expanduser().resolve()
        return interpret_file(path, encoding=encoding)

    @classmethod
    def _export(cls, data: dict, path: (str, Path), encoding='utf-8'):
        path = cls.validate_config_file(path, must_exists=False)
        s = path.suffix.lower()
        if s == '.json':
            path.write_text(json.dumps(data), encoding=encoding)
        else:
            path.write_text(yaml.dump(data), encoding=encoding)
        return path

    def save(self, path: (str, Path)=None, encoding='utf-8'):
        """save config data unde path"""
        if path is None:
            if self.path is not None:
                path = self.path
            else:
                path = params.DEFAULT_CONFIG_FILE
        self._export(self.data, path, encoding=encoding)
        return path

    def reload(self, encoding=None):
        """Reload the config, loosing any change / expansion / replacement you've made, and re-reading files"""
        self._files = {}
        self._load_init(encoding=encoding or self.encoding)
        self._updated = True
        
    def expand(self, path: (str, Path), deep=False, encoding='utf-8', deep_handlers=None):
        """Expand / update config with another config file"""
        data = self._read_config_file(path, encoding=encoding)
        if deep:
            dict_deep_update(self.data, data, handlers=deep_handlers)
        else:
            self.data.update(data)
        self._updated = True

    def replace(self, path: (str, Path)=None, data: dict=None, encoding='utf-8'):
        """Replace current's config data with that from given file or dict"""
        if path is None:
            assert data is not None
            self.data = data
        else:
            self.data = self._read_config_file(path, encoding=encoding)
        self._updated = True

    def __repr__(self):
        if self.path is not None:
            return f'{self.__class__.__name__}("{self.path}")'
        else:
            return f'{self.__class__.__name__}()'

    def __str__(self):
        # return str(self.data)
        return yaml.dump(self.data)
    
    def __contains__(self, item):
        return item in self.data

    def help(self):
        print(self.__doc__)

    # -- update (data) -- 
    def update(self, **kwargs):
        self.data.update(kwargs)
        self._updated = True

    deep_update_handlers = {}

    def deep_update(self, _handlers=None, **kwargs):
        dict_deep_update(self.data, kwargs, handlers=_handlers or self.deep_update_handlers)
        self._updated = True

    # -- sub-config files --
    def add_default_location(self, path: (str, Path), prepend=False):
        if prepend:
            self.default_paths.insert(0, path)
        else:
            self.default_paths.append(path)

    def set_default_download_location(self, path: (str, Path)):
        self.default_download_path = path

    def is_subconfig_file(self, name):
        """Return True if the given config's key defines a sub-config file"""
        x = self.data[name]
        if not hasattr(x, 'get'):
            return False
        is_file = x.get('is_file', self._files.get(name, None))
        if is_file is None:
            # _path key is set when the sub-config file has been fully resolved (downloaded and / or located)
            if set(x).difference({'name', 'url', 'paths', '_path', 'is_file', 'download_dest'}):
                self._files[name] = is_file = False
            else:
                self._files[name] = is_file = True
        return is_file

    def get_subconfig_path(self, name, try_default_paths=True, dest_path=None):
        assert self.is_subconfig_file(name), f'"{name}" entry is not describing a file: cannot get its path'
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
    
    def read_subconfig(self, name, try_default_paths=True, dest_path=None, encoding='utf-8'):
        path = self.get_subconfig_path(name, try_default_paths=try_default_paths, dest_path=None)
        return interpret_file(path, encoding=encoding)

    # -- get --
    def __getitem__(self, item):
        return self.data[item]

    def get(self, name, default=None, try_default_paths=True, dest_path=None, encoding='utf-8', read_file: bool=True):
        try:
            # a sub-config file
            if self.is_subconfig_file(name):
                if read_file:
                    x = self.read_subconfig(name, try_default_paths=try_default_paths, dest_path=dest_path, encoding=encoding)
                else:
                    x = self.get_subconfig_path(name, try_default_paths=try_default_paths, dest_path=dest_path)
            # regular config entry
            else:
                x = self.data[name]
        except KeyError:
            x = default
        return x
        
    # -- set --
    def __setitem__(self, item, value):
        self.data[item] = value
        self._updated = True

    set = __setitem__
    


config = PkgConfig()

# an example to include package's file within the configuration if needed
# config.data.setdefault('stopwords', {'_path': get_resource('pkg/data/stopwords.yml')})


class ConfigValue:
    def __init__(self, node: str, *keys, default=None, setdefault: bool=False, postprocessor: callable=None):
        self.node = node
        self.keys = keys
        self.default = default
        self.setdefault = setdefault
        self.postprocessor = postprocessor
        self._cached = False
        self._value = None

    def _extract_from_config(self, **kw):
        default = kw.get('default', self.default)
        if self.keys:
            x = config.get(self.node, default={})
            for k in self.keys:
                if k in x:
                    x = x[k]
                else:
                    x = default
                    break
        else:
            x = config.get(self.node, default=default)
        if isinstance(x, dict) and self.setdefault:
            x = dict(self.default, **x)

        if self.postprocessor is not None:
            x = self.postprocessor(x)
        self._value = x
        self._cached = True
        return x

    def _get_updated_value(self, **kw):
        if config._updated or not self._cached:
            return self._extract_from_config(**kw)
        else:
            return self._value

    def get(self, key, *args, **kw):
        x = self.value
        assert isinstance(x, dict)
        return x.get(key, *args, **kw)

    def __getitem__(self, item):
        x = self.value
        return x[item]

    def __contains__(self, item):
        return item in self.value

    def __call__(self, *args, **kwargs):
        x = self.value
        assert callable(x)
        return x(*args, **kwargs)

    @property
    def value(self):
        return self._get_updated_value()
