{% set delim = "=" * cookiecutter.app_name|length -%}
{{ delim }}
{{ cookiecutter.app_name }}
{{ delim }}

This is the `{{ cookiecutter.app_name }}` application.


Minimum Requirements
====================

- Python 3.6
- srsly
- requests
- PyYAML >=3.11


Optional Requirements
=====================

.. _pytest: http://pytest.org
.. _Sphinx: http://sphinx-doc.org

- `pytest`_ (for running the test suite)
- `Sphinx`_ (for generating documentation)


Basic Setup
===========

Install for the current user:

.. code-block:: console

    $ python setup.py install --user


Run the application:

.. code-block:: console

    $ python -m {{ cookiecutter.app_name }} --help


Run the test suite:

.. code-block:: console
   
    $ pytest test/


Build documentation:

.. code-block:: console

    $ sphinx-build -b html doc doc/_build/html


Serving API / HTML
==================

Install the required packages:

.. code-block:: console
    
    $ pip install tornado cchardet gunicorn
 
Install your code:

.. code-block:: console

    $ pip install /path/to/your/code
    
Create a running environment:

.. code-block:: console

    $ mkdir run && cd run
    $ CODEROOT=$(python -c 'import {{cookiecutter.project_slug}};print({{cookiecutter.project_slug}}.pkg_info["root"])')
    $ ln -s $CODEROOT/api/wsgi.py .
 
Start the `gunicorn` server:

.. code-block:: console

    $ IP=127.0.0.1
    $ PORT=8000
    $ gunicorn -w 4 -b $IP:$PORT wsgi:server
