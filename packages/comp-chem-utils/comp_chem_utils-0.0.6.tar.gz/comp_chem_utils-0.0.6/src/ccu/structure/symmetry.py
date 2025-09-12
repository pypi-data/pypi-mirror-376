"""Symmetry-related functions and classes.

This class defines the :class:`Transformation` class and useful subclasses
(:class:`~ccu.structure.symmetry.Rotation`,
:class:`~ccu.structure.symmetry.Translation`,
:class:`~ccu.structure.symmetry.Reflection`, and
:class:`~ccu.structure.symmetry.Inversion`)

.. admonition:: Example

    >>> from ase import Atoms
    >>> from ccu.structure.symmetry import check_symmetry, Rotation
    >>> rotation1 = Rotation(90, [0, 0, 1])
    >>> co = Atoms("CO", positions=[[0, 0, 0], [1, 0, 0]])
    >>> rotated = rotation1(co)
    >>> rotated.positions
    array([[0.000000e+00, 0.000000e+00, 0.000000e+00],
          [6.123234e-17, 1.000000e+00, 0.000000e+00]])
    >>> check_symmetry(rotation1, co)
    False
    >>> h2 = Atoms("HH", positions=[[0, 0, 0], [1, 0, 0]])
    >>> rotation2 = Rotation(180, [0, 0, 1])
    >>> check_symmetry(rotation2, h2)
    True
"""

from collections.abc import Iterable
from typing import TYPE_CHECKING
from typing import Protocol

from ase.atoms import Atoms
import numpy as np
from numpy.linalg import norm
from scipy.spatial import transform

from ccu.structure import comparator

if TYPE_CHECKING:
    from numpy.typing import NDArray


class Transformation(Protocol):
    """A protocol for structural transformations.

    In general, implementers of this protocol should preserve the `info`
    dictionary of :class:`~ase.Atoms` objects; however, if changes are made
    to the chemical composition, metadata should be updated as well.
    """

    def __call__(self, structure: Atoms) -> Atoms:
        "Adherents to this protocol should override this method."


class Translation(Transformation):
    r"""A reflection operation.

    This :class:`Transformation` represents the reflection of coordinates
    through a plane.

    Attributes:
        direction: A length 3, 1D :class:`~numpy.ndarray`\ that represents a
            translation.
    """

    def __init__(
        self,
        direction: Iterable[float] | None = None,
    ) -> None:
        r"""Create a reflection operation.

        Args:
            direction: A length 3, 1D :class:`~numpy.ndarray`\ that represents a
                translation. Defaults to the zero vector.
        """
        self.direction = (
            np.zeros(3) if direction is None else np.array(direction)
        )

    def __call__(self, structure: Atoms) -> Atoms:
        """Translate a structure.

        Args:
            structure: An :class:`~atoms.Atoms` instance representing
                structure to be translated.

        Returns:
            A translated copy of the original :class:`~atoms.Atoms` instance.
        """
        new_structure = structure.copy()
        new_structure.positions += self.direction
        return new_structure


class Rotation(Transformation):
    """A rotation operation.

    Attributes:
        angle: A float specifying a rotation angle in degrees.
        axis: A :class:`numpy.ndarray` representing the axis of rotation.

    """

    def __init__(
        self, angle: float = 0.0, axis: Iterable[float] | None = None
    ) -> None:
        """Create a rotation operation.

        Args:
            angle: The angle of rotation. Defaults to 0.0.
            axis: The axis of rotation. Defaults to the positive z-axis.
        """
        self.angle = angle
        self.axis = (
            np.array([0.0, 0.0, 1.0]) if axis is None else np.array(axis)
        )

    def __call__(self, structure: Atoms) -> Atoms:
        """Rotate a structure.

        This rotates the given structure by the angle and about the axis
        specified as attributes of the Rotation object.

        Args:
            structure: An :class:`~atoms.Atoms` instance representing
                structure to be rotated.

        Returns:
            A copy of the original :class:`~atoms.Atoms` instance rotated by
            :attr:`Rotation.angle` about the axis :attr:`Rotation.axis`.

        """
        new_structure = structure.copy()
        new_structure.rotate(self.angle, self.axis)
        return new_structure

    def as_matrix(self) -> "NDArray[np.floating]":
        """The rotation matrix of the symmetry operation."""
        rotvec = self.angle * (self.axis / norm(self.axis))
        rotation = transform.Rotation.from_rotvec(rotvec, degrees=True)
        return rotation.as_matrix()


class Inversion(Transformation):
    r"""An inversion operation.

    This :class:`Transformation` represents the inverson of coordinates
    through a point.

    Attributes:
        point: A length 3, 1D :class:`~numpy.ndarray` that represents the
            inversion point.
    """

    def __init__(self, point: Iterable[float] | None = None) -> None:
        """Instantiate an :class:`Inversion`.

        Args:
            point: A length 3 iterable of floats that represents the inversion
                point.
        """
        self.point = np.zeros(3) if point is None else np.array(point)

    def __call__(self, structure: Atoms) -> Atoms:
        """Invert a structure.

        Args:
            structure: An :class:`.atoms.Atoms` instance representing
                structure to be inverted.

        Returns:
            An inverted copy of the original :class:`.atoms.Atoms` instance.
        """
        new_structure = structure.copy()
        for atom in new_structure:
            atom.position = self.point - (atom.position - self.point)
        return new_structure


class Reflection(Transformation):
    r"""A reflection operation.

    This :class:`Transformation` represents the reflection of coordinates
    through a plane.

    Attributes:
        point: A length 3, 1D :class:`~numpy.ndarray` that represents a point on the
            reflection plane.
        norm: A length 3, 1D :class:`~numpy.ndarray` that represents a vector normal
            to the reflection plane.
    """

    def __init__(
        self,
        point: Iterable[float] | None = None,
        norm: Iterable[float] | None = None,
    ) -> None:
        r"""Create a reflection operation.

        Args:
            point: A length 3 iterable of floats that represents a point on the
                reflection plane. Defaults to the origin.
            norm: A length 3 iterable of floats that represents a vector
                normal to the reflection plane. Defaults to the positive z-axis.
        """
        self.point = np.zeros(3) if point is None else np.array(point)
        self.norm = (
            np.array([0.0, 0.0, 1.0]) if norm is None else np.array(norm)
        )
        self.norm /= np.linalg.norm(self.norm)

    def __call__(self, structure: Atoms) -> Atoms:
        """Reflect a structure.

        This reflects the given structure in the plane defined by `self.point`
        and `self.norm`.

        Args:
            structure: An :class:`~atoms.Atoms` instance representing
                the structure to be reflected.

        Returns:
            A reflected copy of the original :class:`~atoms.Atoms` instance.
        """
        new_structure = structure.copy()
        for atom in new_structure:
            proj = ((atom.position - self.point) @ self.norm) * self.norm
            atom.position -= 2 * proj
        return new_structure


def check_symmetry(
    transform: Transformation, structure: Atoms, tol: float = 5e-2
) -> bool:
    """Check if a structure is symmetric with respect to a transformation.

    Args:
        transform: The :class:`Transformation` with respect to which
            `structure` will be checked for symmetry.
        structure: An :class:`~ase.Atoms` object.
        tol: A float specifying the absolute tolerance for positions.
            Defaults to 5e-2.

    Returns:
        A bool indicating whether or not the given structure possesses
        the symmetry with respect to the given :class:`Transformation`
        subject to the specified tolerance.

    """
    transformed_structure = transform(structure)
    return comparator.Comparator.check_similarity(
        structure, transformed_structure, tol=tol
    )
