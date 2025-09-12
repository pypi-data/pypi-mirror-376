"""Geometry-related functions for atomic structures."""

from collections.abc import Iterable
from collections.abc import Sequence
from itertools import combinations
from itertools import product
import math
from typing import TYPE_CHECKING
from typing import NamedTuple

import ase
from ase.atoms import Atoms
import numpy as np
from numpy.linalg import norm
from numpy.typing import NDArray

from ccu.structure.axisfinder import find_primary_axis
from ccu.structure.axisfinder import find_secondary_axis

if TYPE_CHECKING:
    from numpy.typing import NDArray


def calculate_separation(
    structure1: ase.Atoms, structure2: ase.Atoms
) -> float:
    """Calculates the separation between two Atoms instances.

    The distance is defined as the smallest distance between an atom in one
    structure and an atom in the second structure.

    Args:
        structure1: An :class:`~ase.Atoms` instance.
        structure2: An :class:`~ase.Atoms` instance.

    Returns:
        A float representing the separation between the two structures.

    """
    minimum_separation = math.inf
    structures = product(structure1.positions, structure2.positions)
    for position1, position2 in structures:
        separation = norm(position1 - position2)
        minimum_separation = np.min([minimum_separation, separation])

    return minimum_separation


def calculate_norm(
    points: "list[NDArray[np.floating]]",
    *,
    reverse: bool = False,
) -> "NDArray[np.floating]":
    """Calculate the norm for the *average* plane defined by a set of points.

    Args:
        points: A list of points on a surface. These points should be
            approximately coplanar.
        reverse: Whether or not to reverse the preferred direction for
            the norm. Defaults to False in which case the norm direction is
            determined as follows. If the vector does not lie in the xy-plane,
            then the norm is normalized to have positive z. Otherwise, if the
            vector has a y component, then it is normalized to have positive y.
            and if it has no y component, then it is normalized to have
            positive x. If True, then the norm is normalized to have negative
            z in the above cases.

    Returns:
        A length 3, 1D :class:`numpy.ndarray` representing the unit
        normal vector for the *average* plane defined by `points`.

    Raises:
        ValueError: Less than three non-colinear points provided.
    """
    if len(points) < 2:  # noqa: PLR2004
        msg = "Unable to calculate cross product for less than 2 vectors"
        raise ValueError(msg)

    norms: list[NDArray[np.floating]] = []

    for p1, p2, p3 in combinations(points, r=3):
        vec1 = p1 - p2
        vec2 = p1 - p3
        n = np.cross(vec1, vec2)
        if (n == 0.0).all():
            continue
        n /= norm(n)
        if (
            n[2] < 0
            or (n[2] == 0 and n[1] < 0)
            or (n[1] == n[2] == 0 and n[0] < 0)
        ):
            n *= -1.0
        if reverse:
            n *= -1.0

        norms.append(n)
    if len(norms) == 0:
        msg = f"Unable to find non-colinear lines between points: {points}"
        raise ValueError(msg)
    return np.mean(norms, axis=0)


class MolecularOrientation(NamedTuple):
    r"""The orientation of a molecule.

    A :class:`~ccu.structure.geometry.MolecularOrientation` tuple
    contains the information required to unambiguously orient a molecule
    in space, for example, on an :class:`~ccu.adsorption.sites.AdsorptionSite`.

    Attributes:
        directions: A 2-tuple of length 3, 1D,
            :class:`numpy.ndarrays <numpy.ndarray>` representing the primary and
            secondary orientation directions. These directions orient an
            adsorbate in |site space|_.
        description: A string describing the adsorbate orientation.

    .. |site space| replace:: **site space**
    .. _site space: :ref:`site-space`
    """

    directions: "tuple[NDArray[np.floating], NDArray[np.floating]]"
    description: str


def align(
    adsorbate: Atoms,
    directions: Sequence[Iterable[float]],
    center: Iterable[float] | None = None,
) -> Atoms:
    """Align a molecule according to its primary and secondary axes.

    Args:
        adsorbate: An :class:`~ase.Atoms` representing a molecule.
        directions: A sequence whose first and second elements are length 3,
            iterables of floats representing the primary and secondary
            directions along which `adsorbate` is to be aligned.
        center: A point to remain fixed while aligning `adsorbate`. Defaults
            to the center-of-mass of `adsorbate`.

    Returns:
        A copy of `adsorbate` aligned such that its primary and secondary axes
        coincide with `directions[0]` and `directions[1]`, respectively.
    """
    center = np.array(
        adsorbate.get_center_of_mass() if center is None else center
    )
    v1 = np.array(directions[0])
    v2 = np.array(directions[1])
    new_adsorbate = adsorbate.copy()
    axis1 = find_primary_axis(new_adsorbate)

    # No first orientation for zero-dimensional molecule
    if np.linalg.norm(axis1) == 0:
        return new_adsorbate

    # Orient along primary orientation axis
    new_adsorbate.rotate(axis1, v1, center)

    # Orient using secondary orientation axis
    axis2 = find_secondary_axis(new_adsorbate)

    # No second orientation for one-dimensional molecule
    if np.linalg.norm(axis2) == 0:
        return new_adsorbate

    parallel_component = v1 @ v2 * v1
    perpendicular_component = v2 - parallel_component
    new_adsorbate.rotate(axis2, perpendicular_component, center)

    return new_adsorbate
