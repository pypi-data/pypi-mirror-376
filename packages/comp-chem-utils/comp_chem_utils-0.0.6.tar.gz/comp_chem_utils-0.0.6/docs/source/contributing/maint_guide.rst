Maintenance Guide
=================

This page describes how to perform various maintenance tasks for `ccu`.

Project and Environment Management
------------------------------------

`ccu` uses |hatch|_ for project and environment management. |hatch|_ uses the
|hatchling|_ build system and is configured in the |pyproject.toml|_ file.

There are dedicated `hatch environments`_ for documentation (`docs`),
code-quality (`quality`), testing (`test`), and general development (`default`)
each with their own custom `environment scripts`_. For example, the following
command activates the `docs` environment::

  hatch shell docs

GitLab CI/CD
------------

The following jobs are run on all pushed changes and merge requests:

**quality**
    |pre-commit|_ hooks: |ruff|_, |mypy|_, formatting & security checks

**unit-testing**
    |pytest|_: unit, functional, and regression tests

**doctests**
    test all |doctest|_ examples in documentation

**build-docs**
    |sphinx-build|_: build documentation

**linkcheck**
    check documentation links with the |linkcheck|_ builder

The following jobs are only triggered for commits on `main`:

.. _publish:

**publish**
    upload the package to pypi_

Release Process
---------------

This section walks through the release process.

1. **Determine the version number for the new release**.

   * The version number, `N` is composed of major, minor, and patch components
     (e.g., in the version number `1.2.3`, 1, 2, and 3 are the major, minor,
     and patch components) with optional pre-release labels
   * While under development, `ccu` follows a zero-versioning scheme. When
     stable, `ccu` releases shall be versioned according to |real-semver|_.
   * Pre-releases shall be labeled with "a" and an index, starting from 1
     (e.g., 0.0.1a1).

2. **Create a new branch** called `release-N`.

   * For bug fixes, the branch shall be formed from `main` and eventually
     separately merged into both `main` and `development`.
   * For releases, the branch shall be formed from `development` and eventually
     separately merged into both `main` and `development`.

3. **Finalize changes**. This involves merging any final commits and updating
   the changelog.

4. **Bump the version** using |bump my version|_. ::

    bump-my-version bump --commit VERSION_PART

   where `VERSION_PART` is one of "major", "minor", "patch", or "pre_n".

5. **Build the package locally and test upload** to `test-pypi`_ (optional). ::

    hatch build
    hatch publish -u __token__ -a TOKEN -r test

  `TOKEN` is a valid test-pypi token.

6. **Create and merge a release MR** targeting the `main` branch.
7. **Create a tag** on the `main` branch corresponding to the new version.
   *This will trigger the* |publish|_ *job*.

.. |hatch| replace:: `hatch`
.. _hatch: http://hatch.pypa.io
.. |hatchling| replace:: `hatchling`
.. _hatchling: hatch_
.. |pyproject.toml| replace:: `pyproject.toml`
.. _pyproject.toml: :repo-file:`pyproject.toml`
.. _hatch environments: https://hatch.pypa.io/latest/config/environment/overview
.. _environment scripts: https://hatch.pypa.io/latest/config/environment/overview/#scripts
.. |pre-commit| replace:: `pre-commit`
.. _pre-commit: https://pre-commit.com
.. |ruff| replace:: ``ruff``
.. _ruff: https://docs.astral.sh/ruff/
.. |mypy| replace:: ``mypy``
.. _mypy: http://mypy.readthedocs.io
.. |pytest| replace:: `pytest`
.. _pytest: https://docs.pytest.org
.. |sphinx-build| replace:: `sphinx-build`
.. _sphinx-build: https://www.sphinx-doc.org/en/master/man/sphinx-build.html
.. |doctest| replace:: `doctest`
.. _doctest: https://docs.python.org/3/library/doctest.html
.. |linkcheck| replace:: `linkcheck`
.. |bump my version| replace:: `bump-my-version`
.. _bump my version: https://github.com/callowayproject/bump-my-version
.. _pypi: https://pypi.org
.. _linkcheck: https://www.sphinx-doc.org/en/master/usage/builders/index.html
.. |real-semver| replace:: Realistic Semantic Versioning
.. _real-semver: https://iscinumpy.dev/post/bound-version-constraints/
.. _pipx: http://pipx.pypa.io
.. _create a new merge request: https://gitlab.com/ugognw/python-comp-chem-utils/-/merge-request
.. _test-pypi: http://test.pypi.org/
.. |publish| replace:: `publish`
.. |tag| replace:: `tag`
