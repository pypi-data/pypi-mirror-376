"""DFT-code agnostic standard calculation workflow utilities.

Example:
    Relaxation using a Calculator's internal relaxation algorithms

    .. code-block:: python

        import logging

        from ase.build import bulk
        from ase.calculators.vasp.vasp import Vasp
        from ccu.adsorption.adsorbates import get_adsorbate
        from ccu.workflows.calculation import run_calculation

        logging.basicConfig(level=logging.DEBUG)

        atoms = bulk("Au") * 3
        atoms.center(vacuum=10, axis=2)
        surface_atom = max(atoms, key=lambda a: a.position[2])
        cooh = get_adsorbate("COOH")
        com = cooh.get_center_of_mass()
        site = surface_atom.position + [0, 0, 3]
        direction = site - com

        for atom in cooh:
            atom.position += direction

        atoms += cooh

        atoms.calc = Vasp(...)
        run_calculation(atoms)

Example:
    Relaxation using an ASE :class:`~ase.optimize.optimize.Optimizer`

    .. code-block:: python

        import logging

        from ase.build import molecule
        from ase.calculators.emt import EMT
        from ase.optimize.bfgs import BFGS
        from ccu.workflows.calculation import run_calculation

        logging.basicConfig(level=logging.DEBUG)

        atoms = molecule("CO2")
        atoms.calc = EMT()
        opt = BFGS(atoms)
        run_calculation(atoms, opt=opt, fmax=0.01, steps=10)

Example:
    Relaxation using a VASP calculation followed by Bader analysis.

    .. code-block:: python

        import logging

        from ase.build import molecule
        from ase.calculators.vasp.vasp import Vasp
        from ccu.workflows.calculation import run_bader, run_calculation

        logging.basicConfig(level=logging.DEBUG)

        atoms = molecule("CO2")
        atoms.calc = Vasp(
            algo="Normal",
            ediff=1e-8,
            ediffg=-1e-2,
            encut=450,
            gga="PE",
            ivdw=12,
            kpts=(1, 1, 1),
            nelm=50,
            nsw=50,
            prec="Accurate",
        )
        run_calculation(atoms)
        run_bader(atoms.calc.directory)
"""

from collections.abc import Iterable
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from ase import Atoms
from ase.optimize.optimize import Optimizer
from pymatgen.command_line.bader_caller import bader_analysis_from_path
from pymatgen.command_line.chargemol_caller import ChargemolAnalysis

from ccu import SETTINGS

if TYPE_CHECKING:
    from ase.calculators.calculator import Calculator

logger = logging.getLogger(__name__)


def run_bader(dir_name: str | Path | None = None) -> dict[str, Any]:
    """Run Bader and archive results.

    This function is not meant to be run as a workflow but as a post-processing
    step after calling :func:`ccu.workflows.calculation.run_calculation`.

    Args:
        dir_name: The directory containing charge density files to be used to
            run the Henkelman bader software
            (https://theory.cm.utexas.edu/henkelman/code/bader/).

    Returns:
        A dictionary mapping to charge density analysis data.

    Note:
        Please cite the following if you use this function:

        G. Henkelman, A. Arnaldsson, and H. Jonsson, "A fast and robust
        algorithm for Bader decomposition of charge density", Comput. Mater.
        Sci. 36, 254-360 (2006).

    .. seealso:: :func:`pymatgen.command_line.bader_caller.bader_analysis_from_path`
    """
    dir_name = str(dir_name) if dir_name else str(Path().cwd())
    bader_data = bader_analysis_from_path(dir_name)
    bader_json = Path(dir_name, "bader.json")
    with bader_json.open(mode="w", encoding="utf-8") as file:
        json.dump(bader_data, file, sort_keys=True, indent=4)
    return bader_data


def run_chargemol(
    dir_name: str | Path | None = None,
    atomic_densities: str | Path | None = None,
) -> dict[str, Any]:
    """Run chargemol and archive results.

    This function is not meant to be run as a workflow but as a post-processing
    step after calling :func:`ccu.workflows.calculation.run_calculation`.

    Args:
        dir_name: The directory containing charge density files to be used to
            run the Henkelman bader software
            (https://theory.cm.utexas.edu/henkelman/code/bader/).
        atomic_densities: The path to the directory containing the chargemol
            atomic densities.

    Returns:
        A dictionary mapping to charge density analysis data.

    Note:
        Please cite the following if you use this function:

        Chargemol:
        (1) T. A. Manz and N. Gabaldon Limas, Chargemol program for performing
        DDEC analysis, Version 3.5, 2017, ddec.sourceforge.net.

        DDEC6 Charges:
        (1) T. A. Manz and N. Gabaldon Limas, “Introducing DDEC6 atomic
        population analysis: part 1. Charge partitioning theory and
        methodology,” RSC Adv., 6 (2016) 47771-47801.
        (2) N. Gabaldon Limas and T. A. Manz, “Introducing DDEC6 atomic
        population analysis: part 2. Computed results for a wide range of
        periodic and nonperiodic materials,”
        (3) N. Gabaldon Limas and T. A. Manz, “Introducing DDEC6 atomic
        population analysis: part 4. Efficient parallel computation of net
        atomic charges, atomic spin moments, bond orders, and more,” RSC Adv.,
        8 (2018) 2678-2707.

        CM5 Charges:
        (1) A.V. Marenich, S.V. Jerome, C.J. Cramer, D.G. Truhlar, "Charge
        Model 5: An Extension of Hirshfeld Population Analysis for the Accurate
        Description of Molecular Interactions in Gaseous and Condensed
        Phases", J. Chem. Theory. Comput., 8 (2012) 527-541.

        Spin Moments:
        (1) T. A. Manz and D. S. Sholl, “Methods for Computing Accurate Atomic
        Spin Moments for Collinear and Noncollinear Magnetism in Periodic and
        Nonperiodic Materials,” J. Chem. Theory Comput. 7 (2011) 4146-4164.

        Bond Orders:
        (1) “Introducing DDEC6 atomic population analysis: part 3.
        Comprehensive method to compute bond orders,” RSC Adv., 7 (2017)
        45552-45581.

        DDEC3 Charges:
        (1) T. A. Manz and D. S. Sholl, “Improved Atoms-in-Molecule Charge
        Partitioning Functional for Simultaneously Reproducing the Electrostatic
        Potential and Chemical States in Periodic and Non-Periodic Materials,”
        J. Chem. Theory Comput. 8 (2012) 2844-2867.
        (2) T. A. Manz and D. S. Sholl, “Chemically Meaningful Atomic Charges
        that Reproduce the Electrostatic Potential in Periodic and Nonperiodic
        Materials,” J. Chem. Theory Comput. 6 (2010) 2455-2468.

    .. seealso:: :class:`pymatgen.command_line.chargemol_caller.ChargemolAnalysis`
    """
    dir_name = dir_name or Path().cwd()
    chargemol_data = ChargemolAnalysis(dir_name, atomic_densities).summary
    chargemol_json = Path(dir_name, "chargemol.json")
    with chargemol_json.open(mode="w", encoding="utf-8") as file:
        json.dump(chargemol_data, file, sort_keys=True, indent=4)
    return chargemol_data


def run_calculation(
    atoms: Atoms,
    *,
    opt: Optimizer | None = None,
    properties: Iterable[str] | None = None,
    **opt_params: Any,
) -> tuple[Atoms, Optimizer | None]:
    """Run a calculation.

    This workflow can be used to run a single-point calculation (by omitting
    `opt`), a calculator-internal relaxation, or a relaxation using an ASE
    :class:`~ase.optimize.optimize.Optimizer`.

    Args:
        atoms: An :class:`~ase.Atoms` object with an attached calculator with
            which to run the calculation.
        opt: An ASE :class:`~ase.optimize.optimize.Optimizer` object that can
            optionally be used to perform the relaxation. If None, the
            calculator is used to calculate `properties`.
        properties: An iterable of strings indicating properties to calculate.
            If `opt` is None, defaults to `["energy"]`. Otherwise, defaults to
            `["energy", "forces"]`.
        opt_params: Additional keywords passed on to `opt.run`. Usually,
            `fmax` and/or `steps`.

    Returns:
        The 2-tuple whose first element is the updated
        :class:`~ase.atoms.Atoms` after the calculation and whose second
        element is `opt`.

    Raises:
        RuntimeError: No calculator set for `atoms`.

    Note:
        If relaxing with an ASE optimizer, ensure that `atoms.calc` is
        configured for a single-point calculation in which forces are
        calculated.
    """
    properties = properties or ["energy", "forces"] if opt else ["energy"]

    logger.debug("Running calculation")
    calc: Calculator = atoms.calc

    if calc is None:
        msg = "Oops! It looks like you forget to attach a calculator"
        logger.error(msg)
        raise RuntimeError(msg)

    if opt is not None:
        opt.run(**opt_params)

    directory = calc.directory
    calc.calculate(atoms=atoms, properties=properties)
    atoms.write(Path(directory, SETTINGS.OUTPUT_ATOMS))

    for prop, value in calc.results.items():
        logger.info(f"{prop}: {value!r}")

    logger.info("Successfully ran calculation")
    return atoms, opt
