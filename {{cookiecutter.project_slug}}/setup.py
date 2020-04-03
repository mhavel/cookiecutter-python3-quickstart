#!/usr/bin/env python3
# coding: utf-8

"""
Setup script
"""

from setuptools import find_packages, setup
# from numpy.distutils.core import setup
from pathlib import Path

root = Path(__file__).resolve().parent

f_version = root / 'VERSION'
f_date = root / 'DATE'


# get the version
version = f_version.read_text(encoding='utf-8')

# get the date
date = f_date.read_text(encoding='utf-8')


# optional dependencies


setup(
    name='{{ cookiecutter.app_name }}',
    date=date,

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='description of `{{ cookiecutter.app_name }}`',
    long_description=None,

    # The project's main homepage.
    url='{{ cookiecutter.project_url }}',

    # Author details
    author='{{ cookiecutter.author_name }}',
    author_email='{{ cookiecutter.author_email }}',

    # Choose your license
    license='MIT License',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: dev',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    # What does your project relate to?
    keywords='{{ cookiecutter.keywords }}',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['doc', 'test']),
    # package_data={'{{ cookiecutter.app_name }}': ['data/*.json', 'data/*.css']},

    data_files=[('share/{{cookiecutter.app_name}}', ['VERSION', 'DATE', 'LICENSE'])],
    include_package_data=True,

    # Extension modules
    # ext_modules=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
    #     'console_scripts': [
    #         'cmd_name = path.to.module:function_name',
    #     ],
    # },

    install_requires=['requests', 'srsly', 'PyYAML>=3.11'],

    # to install: pip install "{{cookiecutter.app_name}}"
    extras_require={
        'api': ['hug', 'jinja2', 'cchardet', 'gunicorn[tornado]'],
        'cli': ['plac']
    },
)
