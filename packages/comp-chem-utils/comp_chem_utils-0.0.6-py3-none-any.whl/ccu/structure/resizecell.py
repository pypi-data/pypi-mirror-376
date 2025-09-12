"""Cell resizing tools.

This script resizes the c vector of all the ``.traj`` files in the current
working directory to the specified positive number.
"""

from pathlib import Path

from ase.io import read
from numpy.linalg import norm


def run(structure: Path, length: float):
    """Resize c-vector of structure and centers atoms in cell.

    Args:
        structure: A Path leading to the structure whose cell is to be resized.
            If `structure` points to a file with multiple structures, then
            the final structure is read.
        length: A float specifying the new c-vector of the cell.

    """
    atoms = read(structure)
    atoms = atoms[-1] if isinstance(atoms, list) else atoms
    c_vector = atoms.cell[2]
    c_scale = length / norm(c_vector)
    atoms.cell[2] = c_vector * c_scale
    atoms.center()
    atoms.write(structure)
