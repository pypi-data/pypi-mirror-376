"""DFT-code agnostic standard vibration calculation workflow utilities.

For all other species, :mod:`ccu.workflows.vibration.run_vibration` provides a
standardized, DFT-code-agnostic workflow that can be used to approximate the
Hessian in the ground state, :func:`ccu.workflows.vibration.run_vibration`.
This function is a thin wrapper around the :mod:`ase` thermochemistry utilities
that conveniently logs all relevant thermochemistry data as well as other
information (e.g., forces, frozen atoms, frequencies) to a file.

After running :func:`ccu.workflows.vibration.run_vibration`, one can then run
:func:`ccu.thermo.gibbs.calculate_free_energy` to obtain the entropic
correction (:math:`-TS`) and the vibrational zero-point energy (:math:`ZPE`).
The Gibbs free energy is then calculated as:

.. math::
   :label: gibbs-def

    G = E - TS + ZPE

where :math:`E` is the DFT-calculated energy from
:func:`ccu.workflows.vibration.run_vibration`.

In both of the above cases, one has the option to use the CLI
(:program:`ccu thermo chempot` and :program:`ccu thermo gibbs`)
or the Python API (:func:`ccu.thermo.chempot.calculate` or
:func:`ccu.workflows.vibration.run_vibration` with
:func:`ccu.thermo.gibbs.calculate_free_energy`).

Example:

    .. code:: python

        from ase.build import molecule
        from ase.calculators.emt import EMT
        from ccu.workflows.vibration import run_vibration

        atoms = molecule("CO2")
        atoms.calc = EMT()
        # Only vibrate O atoms
        indices = [a.index for a in atoms if str(a.symbol) == "O"]
        run_vibration(atoms, nfree=4, indices=indices)
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from ase import Atoms
from ase.vibrations.vibrations import Vibrations

if TYPE_CHECKING:
    from ase.calculators.calculator import Calculator
    from ase.vibrations.data import VibrationsData

logger = logging.getLogger(__name__)


def run_vibration(
    atoms: Atoms,
    *,
    name: str = "vib",
    **vib_params: Any,
) -> tuple[Atoms, "VibrationsData"]:
    """Run a vibrational calculation.

    This function is a convenience wrapper around
    :class:`~ase.vibrations.vibrations.Vibrations`.

    Args:
        atoms: An :class:`~ase.atoms.Atoms` object with an attached calculator
            with which to run the vibration calculation.
        name: A string used to name the cache directory, vibration summary,
            vibration mode trajectories, and vibration data files. Defaults to
            ``"vib"``. Note that `name` is passed to the
            :class:`~ase.vibrations.vibrations.Vibrations` constructor.
        vib_params: Additional keyword arguments passed on to the
            :class:`~ase.vibrations.vibrations.Vibrations` constructor.

    Returns:
        The 2-tuple whose first element is the updated
        :class:`~ase.atoms.Atoms` after the calculation and whose second
        element is a :class:`~ase.vibrations.data.VibrationsData` object
        containing the results of the vibration calculation. A
        :class:`~ase.vibrations.vibrations.Vibrations` object can be populated
        from the results directory by instantiating the object with arguments
        corresponding to  `name` and `vib_params` and then calling
        :meth:`!Vibrations.read`.

    Raises:
        RuntimeError: No calculator set for `atoms`.

    .. seealso:: :class:`~ase.vibrations.vibrations.Vibrations`
    """
    logger.debug("Running vibration calculation")
    calc: Calculator = atoms.calc

    if calc is None:
        msg = "Oops! It looks like you forget to attach a calculator"
        logger.error(msg)
        raise RuntimeError(msg)

    vib = Vibrations(
        atoms=atoms, name=Path(calc.directory, name), **vib_params
    )
    vib.run()
    vib.combine()
    with Path(calc.directory, f"{name}.log").open(
        mode="w", encoding="utf-8"
    ) as log:
        vib.summary(log=log)
    zpe = vib.get_zero_point_energy()
    vib_data = vib.get_vibrations()
    vib_data.write(Path(calc.directory, f"{name}.json"))

    logger.info(f"Zero-point energy: {zpe}")
    logger.info(f"Frequencies: {list(vib.get_frequencies())!r}")
    logger.info("Successfully ran vibration calculation")
    return atoms, vib_data
