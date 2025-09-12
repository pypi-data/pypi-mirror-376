=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to a form of Semantic Versioning called
`Realistic (or Practical) Semantic Versioning <https://iscinumpy.dev/post/bound-version-constraints/>`_.

`0.0.6`_ (2025-09-10)
---------------------

Added
~~~~~

* :class:`ccu.adsorption.sites.SiteFinder` protocol and built-in implementations
  :class:`ccu.adsorption.sites.HubSpokeFinder` and
  :class:`ccu.adsorption.sites.Triangulator`
* module-level variables `HUB_TAG`, `SPOKE_TAG`, and `SITE_TAG` for `SiteFinder`
  implementations
* :class:`ccu.adsorption.orientation.AdsorptionCenter`
* :class:`ccu.adsorption.orientation.CenterFactory` and implementations
  `com_centerer()`, `special_centerer()`, `atomic_centerer()`
* :class:`ccu.adsorption.orientation.OrientationFactory` implementations:
  `Transformer` and subclasses (`OctahedralFactory`)
* auto-annotation feature in :mod:`ccu.fancyplots`
* :func:`ccu.fancyplots._gui.annotation.auto_annotate`
* :func:`ccu.structure.geometry.align`
* :class:`ccu.structure.symmetry.Inversion`
* :class:`ccu.structure.symmetry.Reflection`
* :class:`ccu.structure.symmetry.Translation`
* :mod:`ccu.workflows`: a subpackage containing computational workflows

  * :class:`ccu.workflows.infrared`: infrared workflow
  * Users can now seed ``FancyPlots`` with free energies only using the ``--data`` CLI
    option
  * `label` keyword argument to :func:`ccu.workflows.calculation.run_calculation` function

* enable shell completion with ``ccu init``
* allow users to supply a style file to ``ccu fed``

* DEV:
  * `clean` command added to `docs` hatch environment
  * testing and test coverage split into separate commands `test` and `test-cov`

Changed
~~~~~~~

* Atoms objects created from :func:`ccu.adsorption.complexes.generate_complexes`
  have metadata describing the adsorbate, site, and orientation in addition to the
  structure

* Moved ``generate_figure`` to :mod:`ccu.fancyplots.plotting`
* ``bader`` module renamed to ``pop``
* You can now pass the ``annotations`` parameter of
  :func:`ccu.fancyplots.plotting.generate_figure` as a list of appropriately
  typed tuples

* `ccu.adsorption.adsorbatecomplex` renamed to `ccu.adsorption.complex`
* `ccu.adsorption.sitefinder` renamed to `ccu.adsorption.sites`
* `ccu.adsorption.adsorbateorientation` renamed to `ccu.adsorption.orientation`
* `AdsorbateOrientationFactory` replaced with protocol, `OrientationFactory`
* `ccu.adsorption.adsorbateorientation.AdsorbateOrientation` replaced with
  `ccu.structure.geometry.MolecularOrientation`
* `ccu.adsorption.adsorbates.ALL` renamed to `ccu.adsorption.adsorbates.ALL_ADSORBATES`
* :class:`ccu.adsorption.complexes.AdsorbateComplexFactory`:

  * constructor overhauled; see new signature/docstring for details
  * `AdsorbateComplexFactory.next_complex` replaced with
    `AdsorbateComplexFactory.generate_complexes`
  * removed: `AdsorbateComplexFactory.adsorbate_orientations`,
    `AdsorbateComplexFactory.orient_adsorbate`
  * `AdsorbateComplexFactory.place_adsorbate` no longer accepts the `centre`
    argument but instead accepts a `site` argument and shifts the asdorbate position by
    site position
  * `structure` is no longer an attribute but is passed as an argument to
    `.generate_complexes` and `.place_adsorbate`

* :func:`~ccu.adsorption.complexes.generate_complexes`:

  * `generate_complexes` no longer saves the adsorption complexes to files; this can be
    accomplished using :func:`~ccu.adsorption.complexes.write_complexes`; accordingly, the
    `destination` argument was removed

  * a list of `Atoms` objects is returned instead of a list of tuples
  * `special_centres` argument removed and replaced with similar argument, `centers`
  * `symmetric` argument removed and replaced with similar argument, `symmetry`
  * The `finder` argument now accepts adherents to the
    :class:`~ccu.adsorption.sites.SiteFinder` protocol instead of strings (as a consequence,
    the `vertical` argument has been removed since these being returned is controlled by the
    `finder`)
  * `adsorbate_tag` argument has been added

* :mod:`ccu.adsorption.adsorbates`: the `special centres` key has been changed
  to `special_centres`

* documentation refactored (inspired by diataxis_)
* expanded development guide to include dedicated sections for documentation and maintenance
* `calculate_norm` moved to `ccu.structure.geometry`
* **CLI**

  * CLI-related modules/packages have been privatized by appending leading underscores
  * `ccu adsorb`

    * `ccu adsorption place-adsorbate` command renamed to `ccu adsorb`
    * added `--tag` option to `ccu adsorb`
    * `--special-centres` option renamed to `--centers` and changed from flag
      option to value-accepting option
    * `--symmetric` option changed to on/off flag `--no-symmetry/--symmetry`
    * removed `--vertical` option
    * added `--finder` option

* `ccu.structure.symmetry.SymmetryOperation` removed and replaced with
  `ccu.structure.symmetry.Transformation`

* only annotations with text are added in FancyPlots
* GUI subpackage is now private `ccu.fed._gui`

Fixed
~~~~~

* FancyPlots

  * Fixed dashed lines in FED

  * ``AttributeError`` when setting title in
    :func:`ccu.fancyplots.plotting.format_primary_axes`

  * The format of the easter egg has been fixed

* Fix plotting transition states in :mod:`ccu.fancyplots`
* saving annotations in FancyPlots
* duplicate annotations are not added in FancyPlots

Removed
~~~~~~~

* `AdsorbateComplex` class
* `AdsorbateOrientationFactory`
* `ccu.structure.symmetry.Symmetry` and `ccu.structure.symmetry.RotationSymmetry`
* `ccu.hubbard` subpackage

`0.0.5`_ (2024-06-11)
----------------------

Added
~~~~~

* :attr:`xlim <ccu.fancyplots.data.FormattingParameters.xlim>`
  and :attr:`ylim <ccu.fancyplots.data.FormattingParameters.ylim>`

Fixed
~~~~~

* :attr:`xscale <ccu.fancyplots.data.FormattingParameters.xscale>`
  and :attr:`yscale <ccu.fancyplots.data.FormattingParameters.yscale>`
  were incorrectly used to set `xlim` and `ylim`, respectively

* Saving FancyPlots figures now works

* No more duplicate legend labels

* Tooltips are now visible

* Raised exception when trying to show graph when graph already showing

Removed
~~~~~~~

* :func:`!.plotting.plot_solid_lines`

* :func:`!.plotting.plot_dashed_lines`

`0.0.4`_ (2024-06-06)
----------------------

Added
~~~~~

* logging via a rotating file handler

Fixed
~~~~~

* fixed bug where the legend wasn't rendered

* fixed bug in FancyPlots when incrementing number of pathways *after* defining
  the number of steps (see :gitref:`c188153d`)

`0.0.3`_ (2024-06-03)
---------------------

Added
~~~~~

* :mod:`ccu.fancyplots.validation`: classes and functions for validating user input

* :class:`.tooltip.Tooltip`: a robust tooltip class

* :class:`!.gui.root.Windows`: :class:`TypedDict` containing all ``FancyPlots`` subwindows

* :class:`!.gui.root.Sections`: :class:`TypedDict` containing the immediate subframes of a
  ``FancyPlots`` appliction

* :class:`ccu.fancyplots.data`: data models for importing/exporting ``FancyPlots`` data

  * :class:`ccu.fancyplots.data.FancyCache`: simplified interface for importing data into and
    exporting data from ``FancyPlots``

* :mod:`!ccu.fancyplots.gui.annotation`: GUI elements for the annotation section

* :mod:`!ccu.fancyplots.gui.energy`: GUI elements for the free energy declaration window

* :class:`!ccu.fancyplots.gui.formatting`: GUI elements for the formatting parameters section

* :class:`!ccu.fancyplots.gui.frames`: custom GUI elements with built-in validation and custom
  event generation (``<<Validation>>``)

* :mod:`!ccu.fancyplots.gui.instructions`: GUI elements for displaying instructions

* :mod:`!ccu.fancyplots.gui.mechanism`: GUI elements for defining reaction mechanisms

* :mod:`!ccu.fancyplots.gui.palette`: GUI elements for displaying the :mod:`matplotlib` colour
  palette

* :mod:`ccu.fancyplots.styles`: custom Tkinter styles for themed widgets

* :func:`!ccu.fancyplots.gui.utils.open_image`: open Tkinter-compatible image

* :func:`!ccu.fancyplots.gui.utils.print_easter_egg`: print Easter egg

* :mod:`ccu.fancyplots.validation`: lightweight, Pydantic-like validation from type-hints

* :program:`ccu adsorption place-adsorbate`: ``--list`` CLI option

* :class:`ccu.thermo.chempot.ChemPotDatabase`: database of chemical potential
  parametrization data

* :class:`ccu.thermo.chempot.ChemPotCalculator`: class encapsulating chemical
  potential calculation logic

* logging and terminal printing control for all CLI commands via :option:`ccu --log-level`,
  :option:`ccu-thermo-gibbs --log-file`, :option:`ccu --verbose`, and :option:`ccu --quiet`
  CLI options that can be passed alongside any subcommand options

* :mod:`!ccu.cli.utils`: utilities for CLI commands

Changed
~~~~~~~

* ``FancyPlots`` re-written with ``ttk``

* :class:`!.root.FancyPlotsGUI` replaces :class:`!Root`

* :class:`!~ccu.fancyplots.gui.root.FancyPlotsGUI` refactored to encompass all GUI elements as children

* redefined as :class:`!~tkinter.ttk.LabelFrame` or :class:`!~tkinter.Frame`  subclasses

  * :class:`!ccu.fancyplots.gui.annotation.AnnotationSection`

  * :class:`!ccu.fancyplots.gui.footer.FooterSection`

* redefined as :class:`!~tkinter.Toplevel` subclasses

  * :class:`!ccu.fancyplots.gui.energy.EnergyWindow`

  * :class:`!ccu.fancyplots.gui.fed.FreeEnergyDiagram`

* :func:`!ccu.fancyplots.gui.menu.make_textmenu` renamed to
  :func:`!ccu.fancyplots.gui.menu.create_edit_menu`

* :func:`!ccu.fancyplots.gui.menu.show_textmenu` renamed to
  :func:`!ccu.fancyplots.gui.menu.show_edit_menu` and re-written as factory

* :mod:`!ccu.fancyplots.gui.fancyplots` renamed to :mod:`!ccu.fancyplots.gui.plotting`

  * functions no longer depend on global variables

  * main function (``init``) renamed to :func:`!ccu.fancyplots.gui.plotting.generate_figure`

* ``ccu.fancyplots.gui.utils.mouse_coordinates`` moved to instance method
  :meth:`!ccu.fancyplots.gui.fed.FreeEnergyDiagram.mouse_coordinates`

* ``ccu thermo chempot-calculator`` refactored and renamed to ``ccu thermo chempot``; parametrized
  data moved to resource; CLI options added for molecule, temperature and pressure

Removed
~~~~~~~
* :class:`!.tooltip.ToolTip`: use :class:`!ccu.fancyplots.gui.tooltip.Tooltip`

* :mod:`!ccu.fancyplots.gui.defaults`: use :class:`ccu.fancyplots.data` instead

* ``ccu.fancyplots.gui.utils``

  * ``.add_path``

  * ``.add_text_converter``

  * ``.convert_path_to_list``

  * ``.get_path``

  * ``.obtain_boxsizes``

* ``ccu-thermo-gibbs --verbose`` and ``ccu-bader-sum --verbose``
  (use :option:`ccu --verbose` instead; e.g., ``ccu --verbose thermo gibbs``)

* Reordering steps in FancyPlots is temporarily removed until further notice

`0.0.2`_ (2024-05-23)
---------------------

Added
~~~~~

* Changelog descriptions for release 0.0.1.

* ``ccu structure permute``: create permutations of atoms within a structure

* ``ccu fed``: a GUI utility for creating free energy diagrams

* ``ccu adsorption place-adsorbate`` now includes additional intermediates

* ``ccu bader``: CLI utility for Bader charge analysis

* :mod:`!ccu.hubbard`: calculation of Hubbard U parameter by the linear response method of `M. Cococcioni and S. de Gironcoli, Phys. Rev. B 71, 035105 (2005) <https://itp.tugraz.at/LV/sormann/TFKP4/papers/LDA+U/Cococcioni_02_Fe_LDA+U.pdf>`_.

* :mod:`!ccu.relaxation`: standard function for running DFT calculation with ASE

* :mod:`!ccu.thermo`: CLI utility and Python API for thermochemistry

Changed
~~~~~~~

* Format changelog in `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_ style.

* Testing with Tox to Nox

* Drop `pylint`_ for `Ruff`_ + `Mypy`_

* :class:`!.sitefinder.MOFSiteFinder` no longer includes between-linker sites by default,
  pass ``between_linkers=True`` to obtain previous behaviour

`0.0.1`_ (2023-06-22)
---------------------

Added
~~~~~

* First release on PyPI.

* Created `ccu.adsorption` and `ccu.structure` subpackages and unit tests

.. _`0.0.6`: https://gitlab.com/ugognw/python-comp-chem-utils/-/compare/v0.0.5...v0.0.6
.. _`0.0.5`: https://gitlab.com/ugognw/python-comp-chem-utils/-/compare/v0.0.4...v0.0.5
.. _`0.0.4`: https://gitlab.com/ugognw/python-comp-chem-utils/-/compare/v0.0.3...v0.0.4
.. _`0.0.3`: https://gitlab.com/ugognw/python-comp-chem-utils/-/compare/v0.0.2...v0.0.3
.. _`0.0.2`: https://gitlab.com/ugognw/python-comp-chem-utils/-/compare/v0.0.1...v0.0.2
.. _`0.0.1`: https://gitlab.com/ugognw/python-comp-chem-utils/-/tree/v0.0.1?ref_type=tags
.. _pylint: https://pylint.readthedocs.io/en/stable/
.. _Ruff: https://docs.astral.sh/ruff/
.. _Mypy: https://mypy.readthedocs.io/en/stable/
.. _diataxis: https://diataxis.fr
