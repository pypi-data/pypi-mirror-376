Calculating thermodynamic properties
------------------------------------

The :mod:`ccu.thermo.chempot` module features a DFT-parametrized calculator
that can be used to calculate chemical potentials for a number of molecules.
The calculator can be accessed via the subcommand ``ccu thermo chempot``.

.. code-block:: console

    $ ccu thermo chempot CO2 -t 298.15 -p 1.01325
    ================================
    CO2 // 298.15 K // 1.01325 bar
    ================================
            G = zpe + Δμ(0 → T)
        zpe =        0.306 eV
    Δμ(0 → T) =       -0.582 eV
            G =       -0.276 eV
    --------------------------------

The molecules for which the calculator is parametrized can be listed with the
``-l/--list`` CLI option

.. code-block:: console

    $ ccu thermo chempot -l
    CO2
    CO
    H2
    H2O
    NH3
    O2
    NO
    NO2
    CH4
    H2O2
    N2

From within Python, the :func:`ccu.thermo.chempot.calculate` function exposes
the same functionality:

>>> from ccu.thermo.chempot import calculate
>>> calculate("CO2", temperature=298.15, pressure=1.01325)
(-0.5815..., 0.306)
