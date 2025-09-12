"""This module defines utilities for charge difference analysis.

.. admonition:: Example

    .. code-block:: python

        import logging
        from ase.build import bulk
        from ase.calculators import Vasp
        from ccu.adsorption.adsorbates import get_adsorbate
        from ccu.workflows.vcdd import run_vcdd

        logging.basicConfig(level=logging.DEBUG)

        atoms = bulk("Au") * 3
        atoms.center(vacuum=10, axis=2)
        surface_atom = max(atoms, key=lambda a: a.position[2])
        co = get_adsorbate("CO")
        co.set_tags([-99] * len(co))
        com = co.get_center_of_mass()
        site = surface_atom.position + [0, 0, 3]
        direction = site - com

        for atom in co:
            atom.position += direction

        atoms += co

        atoms.calc = Vasp(...)
        run_vcdd(atoms, tags=[-99])
"""

import logging
from pathlib import Path

from ase import Atoms

logger = logging.getLogger(__name__)


def _perform_calc(atoms: Atoms) -> None:
    _ = atoms.get_potential_energy()
    atoms.write(Path(atoms.calc.directory).joinpath("final.traj"))


def run_vcdd(
    atoms: Atoms,
    tags: list[int],
) -> None:
    """Perform a set of calculations for charge density difference analysis.

    Args:
        atoms: An Atoms object with an attached calculator with which to run
            the relaxation calculation.
        tags: A list of integers, each identifying a subsystem. A
            calculation will be performed for each tag as well as for all
            atoms not matching any given tags.

    Raises:
        ValueError: No atoms with a specified tag.
    """
    # Set directory for reference charge density
    atoms.calc.set(directory="ref")
    _perform_calc(atoms)
    logger.info("Reference calculation complete")

    # Set directories for subtrahend charge densities
    tag_indices = [[a.index for a in atoms if a.tag == tag] for tag in tags]
    tag_indices.append([a.index for a in atoms if a.tag not in tags])

    for i, indices in enumerate(tag_indices):
        if not indices:
            msg = "No atoms in subystem: %i. Skipping..."
            logger.warning(msg, i)
            continue

        subsystem = atoms[indices]
        subsystem.calc = atoms.calc
        subsystem.calc.set(directory=f"subsystem_{i}")
        _perform_calc(subsystem)
        logger.info(f"Subsystem {i} calculation complete")
