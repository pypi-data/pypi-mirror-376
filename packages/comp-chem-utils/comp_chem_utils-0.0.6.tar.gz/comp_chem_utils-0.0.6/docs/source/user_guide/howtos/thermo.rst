===============
Thermochemistry
===============

Supposing that you have run a vibrational calculation using `ase`
(either directly using the :class:`ase.vibrations.Vibrations` class
or indirectly using :func:`ccu.workflows.vibration.run_vibration` function),
then then thermochemical results can be retrived using the
:func:`ccu.thermo.gibbs.calculate_free_energy` function:

.. code:: python

    from pathlib import Path

    with Path('vib.txt') as vib_file:
        ts, zpe, freq = calculate_free_energy(
            vib_file=vib_file,
            approximation="HARMONIC"
        )

The above code assumes that you have written the vibrational energies
from the vibrational calculation to a file called `vib.txt`.
