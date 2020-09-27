# coding: utf-8

"""
YAML tools
"""

# -- try ruamel
try:
    # from ruamel.yaml import YAML as yaml
    from ruamel import yaml
    yaml_lib = 'ruamel'

# -- PyYaml
except ImportError:
    import yaml
    yaml_lib = 'pyyaml'
    try:
        # prefer C libs
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper


def load_ruamel(s):
    return yaml.load(s)


def safe_load_ruamel(s):
    return yaml.safe_load(s)


def dump_ruamel(x, indent=2, default_flow_style=False, explicit_start=False, explicit_end=False):
    return yaml.dump(x, default_flow_style=default_flow_style, explicit_start=explicit_start, indent=indent, explicit_end=explicit_end)


def load_pyyaml(s):
    return yaml.load(s, Loader=Loader)


def safe_load_pyyaml(s):
    return yaml.safe_load(s)


def dump_pyyaml(x, indent=2, default_flow_style=False, explicit_start=False, explicit_end=False):
    return yaml.dump(x, Dumper=Dumper, default_flow_style=default_flow_style, explicit_start=explicit_start, indent=indent, explicit_end=explicit_end)


if yaml_lib == 'ruamel':
    load = load_ruamel
    dump = dump_ruamel
    safe_load = safe_load_ruamel

else:
    load = load_pyyaml
    dump = dump_pyyaml
    safe_load = safe_load_pyyaml
