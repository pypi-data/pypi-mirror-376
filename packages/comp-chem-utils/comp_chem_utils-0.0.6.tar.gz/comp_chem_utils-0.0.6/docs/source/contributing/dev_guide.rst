=================
Development Guide
=================

This page describes how to set up your environment for developing `ccu`.

.. _setting-up:

Setting Up
----------

Follow these steps to set up your local environment to develop |ccu|_.

1. Fork |ccu|_ on GitLab (look for the "Fork" button).

2. Clone your fork locally::

    git clone git@gitlab.com:YOURGITLABNAME/python-comp-chem-utils.git
    cd python-comp-chem-utils

3. Install |hatch|_ (optional).\ [1]_

4. Install `ccu` into a virtual environment with development extras::

    python3 -m venv .venv
    source .venv/bin/activate
    pip install .[dev,docs,test]

   If |hatch|_ is installed, you can instead run::

    hatch shell

5. Install the |pre-commit|_ hooks (optional):\ [2]_ ::

    pre-commit install --hook-type pre-commit

Development Worklow
-------------------

Follow these steps to contribute your first changes to |ccu|_.

1. Make sure your environment is :ref:`set up <setting-up>`.

2. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

3. Commit your changes, push them to your remote and
   `create a new merge request`_ (see the :ref:`mr-guidelines`)::

    git commit -m 'A descriptive commit message'
    git push origin

.. admonition:: Writing Good Commit Messages

    Focus on "what" changed and "why". The "how" should be self-explanatory
    from the diff.

.. _mr-guidelines:

Merge Request Guidelines
------------------------

If you need some code review or feedback while you're developing the code, please
`create a new merge request`_. Before your changes can be merged, please ensure
that:

1. Tests are passing (run |pytest|_ or `hatch run test:test`).

2. Documentation is updated when there's new API, functionality, etc.

3. New functionality is accompanied by the appropriate unit tests.

4. `CHANGELOG.rst` is updated with nontrivial changes.

5. Your name is listed in `AUTHORS.rst`.

6. The correct branch is targeted.

   * `main`: bug fixes and documentation changes for the current version

   * `development`: new features and any breaking changes

Coding Standards
----------------

`ccu` closely follows the `Google style guide for Python`_.

* All public functions must have docstrings and type-hints.

* Format your code with |ruff|_.

* Docstrings must be written in the no-types version of Google-style docstrings.

* When writing new documentation, consider the principles of diataxis_.

.. _mr_guidelines:

Code-Quality
~~~~~~~~~~~~

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v0.json
    :target: https://github.com/charliermarsh/ruff

.. image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: http://mypy-lang.org/

To run code-quality checks, run::

    pre-commit run --all-files

or::

    hatch run quality:quality

This will run |ruff|_ and |mypy|_ along with other formatting and security checks.

Tests
~~~~~

`ccu` uses the |pytest|_ testing framework.

To run tests on the current Python version, run::

    pytest

To run tests on a specific Python version (version must be present), run::

    hatch run test.pyX.Y:test

where `X` and `Y` are the major and minor Python version number, respectively.

To run tests on all supported Python versions (versions must be present), run::

    hatch run test:test

.. [1] (|hatch|_ helps with project and environment management.)
.. [2] Running the |pre-commit|_ hooks as part of the development process is recommended
       as it is a cheap way for you to catch errors in your code before CI.

.. |ccu| replace:: ``ccu``
.. _ccu: https://gitlab.com/ugognw/python-comp-chem-utils/
.. |hatch| replace:: `hatch`
.. _hatch: http://hatch.pypa.io
.. |pre-commit| replace:: `pre-commit`
.. _pre-commit: https://pre-commit.com
.. _create a new merge request: https://gitlab.com/ugognw/python-comp-chem-utils/-/merge-request
.. |pytest| replace:: `pytest`
.. _pytest: https://docs.pytest.org/
.. _Google-style docstrings: https://google.github.io/styleguide/pyguide.html
.. _Google style guide for Python: https://google.github.io/styleguide/pyguide.html
.. |ruff| replace:: ``ruff``
.. _ruff: https://docs.astral.sh/ruff/
.. _diataxis: https://diataxis.fr
.. |mypy| replace:: ``mypy``
.. _mypy: http://mypy.readthedocs.io
