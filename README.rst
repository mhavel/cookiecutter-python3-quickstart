###################################
Python 3 Quick-start Project Template
###################################

.. _travis: https://travis-ci.org/mhavel/cookiecutter-python3-quickstart
.. |travis.png| image:: https://travis-ci.org/mhavel/cookiecutter-python3-quickstart.png
   :alt: Travis CI build status
   :target: `travis`_

|travis.png|

.. _Cookiecutter: http://cookiecutter.readthedocs.org
.. _Python Packaging User Guide: https://packaging.python.org/en/latest/distributing.html#configuring-your-project
.. _Packaging a Python library: http://blog.ionelmc.ro/2014/05/25/python-packaging


This is a `Cookiecutter`_ template for quickly creating a Python 3 project.

The project layout is based on the `Python Packaging User Guide`_. The current
conventional wisdom forgoes the use of a source directory, but moving the
package out of the project root provides several advantages (*cf.*
`Packaging a Python library`_).


================
Project Features
================

.. _pytest: http://pytest.org
.. _Sphinx: http://sphinx-doc.org
.. _MIT License: http://choosealicense.com/licenses/mit

- Python 3.6+
- `MIT License`_
- `pytest`_ test suite
- `Sphinx`_ documentation


====================
Application Features
====================

.. _YAML: http://pyyaml.org/wiki/PyYAML

- package's tools (information, data resources / files, importer, config)
- useful python 3 utilities (strings, namespaces, augmented dict, decorators, patching, downloads, mapping)
- optional hug Rest API with Jinja2 HTML templates


=====
Usage
=====

.. _GitHub: https://github.com/mhavel/cookiecutter-python3-quickstart


Install Python requirements for using the template:

.. code-block:: console

  $ python -m pip install --user --requirement=requirements.txt


Create a new project directly from the template on `GitHub`_:

.. code-block:: console

  $ cookiecutter gh:mhavel/cookiecutter-python3-quickstart
