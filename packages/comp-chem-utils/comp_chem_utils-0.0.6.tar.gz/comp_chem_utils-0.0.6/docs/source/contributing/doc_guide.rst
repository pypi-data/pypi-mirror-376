Contributing Documentation
==========================

The `ccu` documentation is written in |RST|_, built with sphinx_, and hosted
on ReadTheDocs_. To build the documentation locally, ensure that the `docs`
extra is installed::

    pip install .[docs]

Building the Documentation
--------------------------

To build the documentation, run::

    sphinx-build -b html docs/source docs/build

If you have |hatch|_ installed, you can simply run::

    hatch run docs:docs

Viewing the Documentation
-------------------------

To simply view the built webpage, you can launch a local web server with::

    python -m http.server -d docs/build 8000

You should now be able to view the documentation by entering
`http://localhost:8000` into your browser.

To automatically reload the documentation upon changes to `docs/source` or
`src/ccu`, run::

    sphinx-autobuild -b html --watch src/ccu docs/source docs/build

or, if you have |hatch|_ installed, you can simply run::

    hatch run docs:serve

Documentating API Changes
-------------------------

`ccu`\ 's API is documented automatically from docstrings. If you add packages
or modules, be sure to run `sphinx-apidoc` as part of the MR. Specifically, you
can run the following from the projet root::

    sphinx-apidoc --private -d 3 --separate --remove-old --force --module-first -H 'Package Index' --templatedir docs/source/user_guide/reference/_templates -fo docs/source/user_guide/reference/api src/ccu '**/settings*'

or, if you have |hatch|_ installed::

    hatch run docs:apidoc

Tips
~~~~

Here are some tips for writing good documentation:

* Write with the purpose in mind. To what extent will the documentation serve
  to educate? To what extent will the documentation serve to facilitate doing?
  In the spirit of diataxis_, is the documentation a tutorial, how-to,
  explanation, or reference?

* Use `cross-references`_! They make it easier for users to navigate between
  different pages.

* Please use the no-types version of `Google-style docstrings`_ to document
  items:

.. code-block:: python

    def my_function(arg: Foo) -> Bar:
        """Do important stuff.

        More detailed info here, in separate paragraphs from the subject line.
        Use proper sentences -- start sentences with capital letters and end
        with periods.

        Follow with Google-style sections:

        Args:
            arg: A :class:`Foo` representing foos.

        Returns:
            A :class:`Bar`.

        .. versionadded:: 6.0
        """

* Type-hint all public functions/classes/modules!

* Write tutorials and how-tos as doctests_, where possible. Doctests are run
  as part of CI, so doctests offer a built-in way to check that
  tutorials/how-tos still work. You can verify that doctests work as expected
  using the `doctest` sphinx builder_. Run::

    sphinx-build -b doctest docs/source docs/build

or::

    hatch run docs:linkcheck

* Verify that links work as expected using the `linkcheck` sphinx builder_. Run::

    sphinx-build -b linkcheck docs/source docs/build

or::

    hatch run docs:linkcheck

.. seealso::

    |apidoc|_
        Sphinx extension for generating API documentation from Python packages

    |autodoc|_
        Sphinx extension for including documentation from docstrings

    |intersphinx|_
        Sphinx extension for linking to other projects' documentation

    |napoleon|_
        Sphinx extension for supporting for NumPy and Google style docstrings

.. |RST| replace:: reStructuredText
.. _RST: https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html
.. _sphinx: https://www.sphinx-doc.org/
.. _ReadTheDocs: http://readthedocs.org
.. |hatch| replace:: `hatch`
.. _hatch: http://hatch.pypa.io
.. _Google-style docstrings: https://google.github.io/styleguide/pyguide.html
.. _doctests: https://docs.python.org/3/library/doctest.html#option-flags
.. |apidoc| replace:: **apidoc**
.. _apidoc: https://www.sphinx-doc.org/en/master/usage/extensions/apidoc.html
.. |autodoc| replace:: **autodoc**
.. _autodoc: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
.. |napoleon| replace:: **napoleon**
.. _napoleon: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
.. _builder: https://www.sphinx-doc.org/en/master/usage/builders/index.html
.. _diataxis: https://diataxis.fr
.. _cross-references: https://www.sphinx-doc.org/en/master/usage/referencing.html
.. |intersphinx| replace:: **intersphinx**
.. _intersphinx: https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
