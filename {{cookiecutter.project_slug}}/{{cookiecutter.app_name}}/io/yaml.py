
# coding: utf-8

"""
YAML tools
"""

from pathlib import Path
from typing import Union

from .common import check_suffix_, check_type_

# -- try ruamel
try:
    # from ruamel.yaml import YAML as yaml
    from ruamel import yaml
    yaml_lib = 'ruamel'
    try:
        # prefer C libs
        from ruamel.yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from ruamel.yaml import Loader, Dumper

# -- PyYaml
except ImportError:
    import yaml
    yaml_lib = 'pyyaml'
    try:
        # prefer C libs
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper


NAME = 'yaml'
VALID_EXTENSIONS = ('.yml', '.yaml')
DEFAULT_EXTENSION = '.yaml'
VALID_TYPES = None


def check_suffix(path: Union[Path, str], raise_error: bool=False):
    return check_suffix_(path, VALID_EXTENSIONS, DEFAULT_EXTENSION, raise_error=raise_error)


def check_type(data, raise_error=True):
    return check_type_(data, NAME, VALID_TYPES, raise_error=raise_error)


def load_ruamel(s, version=None):
    return yaml.load(s, Loader=Loader, version=version)


def safe_load_ruamel(s):
    return yaml.safe_load(s)


# def dump_ruamel(x, indent=2, default_flow_style=False, explicit_start=False, explicit_end=False):
#     return yaml.dump(x, default_flow_style=default_flow_style, explicit_start=explicit_start, indent=indent, explicit_end=explicit_end, Dumper=Dumper)

def dump_ruamel(x, indent=2, default_flow_style=False, explicit_start=False, explicit_end=False, allow_unicode=True, encoding='utf-8',
    version=None):
    return yaml.dump(x, default_flow_style=default_flow_style, explicit_start=explicit_start,
        indent=indent, explicit_end=explicit_end, Dumper=Dumper, allow_unicode=allow_unicode, encoding=encoding, version=None)


def load_pyyaml(s):
    return yaml.load(s, Loader=Loader)


def safe_load_pyyaml(s):
    return yaml.safe_load(s)


def dump_pyyaml(x, indent=2, default_flow_style=False, explicit_start=False, explicit_end=False):
    return yaml.dump(x, Dumper=Dumper, default_flow_style=default_flow_style, explicit_start=explicit_start, indent=indent, explicit_end=explicit_end).encode()


if yaml_lib == 'ruamel':
    load = load_ruamel
    dump = dump_ruamel
    safe_load = safe_load_ruamel
    del load_pyyaml, safe_load_pyyaml, dump_pyyaml

else:
    load = load_pyyaml
    dump = dump_pyyaml
    safe_load = safe_load_pyyaml
    del load_ruamel, safe_load_ruamel, dump_ruamel


def read(path: Union[str, Path], container=None, fix_suffix: bool=True, **kw):
    path = check_suffix(path, raise_error=not fix_suffix)
    data = load(path.read_text(), **kw)
    if container is not None:
        data = container(data)
    return data


def write(x, path: Union[str, Path], fix_suffix: bool=True, **kw):
    path = check_suffix(path, raise_error=not fix_suffix)
    return path.write_bytes(dump(x, **kw))
