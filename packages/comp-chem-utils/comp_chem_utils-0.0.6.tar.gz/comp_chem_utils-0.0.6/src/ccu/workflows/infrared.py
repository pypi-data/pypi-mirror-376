"""DFT-code agnostic standard infrared calculation workflow utilities.

Example:

    .. code:: python

        from ase.build import molecule
        from ase.calculators.emt import EMT
        from ccu.workflows.infrared import run_infrared

        atoms = molecule("CO2")
        atoms.calc = EMT()
        # Only vibrate O atoms
        indices = [a.index for a in atoms if str(a.symbol) == "O"]
        run_infrared(atoms, nfree=4, indices=indices)
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from ase import Atoms
from ase.vibrations.infrared import Infrared

if TYPE_CHECKING:
    from ase.calculators.calculator import Calculator
    from ase.vibrations.data import VibrationsData

logger = logging.getLogger(__name__)


def run_infrared(
    atoms: Atoms, *, name: str = "ir", **ir_params: Any
) -> tuple[Atoms, "VibrationsData"]:
    """Run an infrared calculation.

    This function is a convenience wrapper around
    :class:`~ase.vibrations.infrared.Infrared`.

    Args:
        atoms: An :class:`~ase.Atoms` object with an attached calculator
            with which to run the infrared calculation.
        name: A string used to name the cache directory, ir summary,
            ir mode trajectories, and ir data files. Defaults to
            ``"ir"``. Note that `name` is passed to the
            :class:`~ase.vibrations.infrared.Infrared` constructor.
        ir_params: Additional keyword arguments passed on to the
            :class:`~ase.vibrations.infrared.Infrared` constructor.

    Returns:
        The 2-tuple whose first element is the updated
        :class:`~ase.atoms.Atoms` after the calculation and whose second
        element is a :class:`~ase.vibrations.data.VibrationsData` object
        containing the results of the infrared calculation. A
        :class:`~ase.vibrations.infrared.Infrared` object can be populated
        from the results directory by instantiating the object with arguments
        corresponding to  `name` and `ir_params` and then calling
        :meth:`!Infrared.read`.

    Raises:
        RuntimeError: No calculator set for `atoms`.
    """
    logger.debug("Running infrared calculation")
    calc: Calculator = atoms.calc

    if calc is None:
        msg = "Oops! It looks like you forget to attach a calculator"
        logger.error(msg)
        raise RuntimeError(msg)

    ir = Infrared(atoms=atoms, name=Path(calc.directory, name), **ir_params)
    ir.run()
    ir.combine()
    with Path(calc.directory, f"{name}.log").open(
        mode="w", encoding="utf-8"
    ) as log:
        ir.summary(log=log)
    ir_data = ir.get_vibrations()
    ir_data.write(Path(calc.directory, f"{name}.json"))

    logger.info(f"Frequencies: {list(ir.get_frequencies())!r}")
    logger.info("Successfully ran infrared calculation")
    return atoms, ir_data
