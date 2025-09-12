"""Interfaces for orienting adsorbates on adsorption sites."""

from collections.abc import Iterable
from typing import TYPE_CHECKING
from typing import NamedTuple
from typing import Protocol

from ase.atoms import Atoms
import numpy as np

from ccu.adsorption.sites import AdsorptionSite
from ccu.structure.axisfinder import get_axes
from ccu.structure.comparator import Comparator
from ccu.structure.geometry import MolecularOrientation
from ccu.structure.geometry import align
from ccu.structure.symmetry import Reflection
from ccu.structure.symmetry import Rotation
from ccu.structure.symmetry import Transformation

if TYPE_CHECKING:
    from numpy.typing import NDArray


class AdsorptionCenter(NamedTuple):
    """A tuple representing a point in space used to center an adsorbate.

    Attributes:
        position: A length 3, 1D :class:`numpy.ndarray` of floats representing
            the position of the adsorption center in space.
        description: A description of the adsorption center (e.g., `"on C1"`).
    """

    position: "NDArray[np.floating]"
    description: str


class CenterFactory(Protocol):
    r"""A Callable that generates :class:`AdsorptionCenters <ccu.adsorption.orientation.AdsorptionCenter>`.

    The :class:`numpy.ndarrays <numpy.ndarray>` returned when calling
    implementers of this protocol should identify different points used to
    center an adsorbate.
    """

    def __call__(self, adsorbate: Atoms) -> list[AdsorptionCenter]:
        """Protocol adherents should implement this function."""


def com_centerer(adsorbate: Atoms) -> list[AdsorptionCenter]:
    """A :class:`CenterFactory` for centering adsorbates with their COM.

    Args:
        adsorbate: An :class:`~ase.Atoms` object.

    Returns:
        A list containing a single
         :class:`AdsorptionCenters <AdsorptionCenter>` corresponding to the
         centre-of-mass of `adsorbate`.
    """
    return [AdsorptionCenter(adsorbate.get_center_of_mass(), "COM")]


def special_centerer(adsorbate: Atoms) -> list[AdsorptionCenter]:
    """A :class:`CenterFactory` that returns special centers.

    Special centers must be identified by the key `"special_centers"` in
    `adsorbate.info`.

    Args:
        adsorbate: An :class:`~ase.Atoms` object.

    Returns:
        A list of special centers--relative to the adsorbate center of mass.
    """
    if "special_centers" in adsorbate.info and (
        indices := adsorbate.info["special_centers"]
    ):
        centers: list[AdsorptionCenter] = []
        for index in indices:
            description = f"{adsorbate[index].symbol} {index}"
            center = AdsorptionCenter(adsorbate[index].position, description)
            centers.append(center)
        return centers

    return [AdsorptionCenter(adsorbate[0].position, "0")]


def atomic_centerer(adsorbate: Atoms) -> list[AdsorptionCenter]:
    """A :class:`CenterFactory` that returns atomic centers.

    Args:
        adsorbate: An :class:`~ase.Atoms` object.

    Returns:
        A list of :class:`AdsorptionCenters <AdsorptionCenter>` representing the
        atomic positions of `adsorbate` with descriptions in the form
        `SYMBOL_INDEX`, where `SYMBOL` and `INDEX` are the atom's chemical
        symbol and index, respectively.
    """
    return [
        AdsorptionCenter(a.position, f"{a.symbol} {a.index}")
        for a in adsorbate
    ]


class OrientationFactory(Protocol):
    r"""A Callable that generates :class:`MolecularOrientations <ccu.structure.geometry.MolecularOrientation>`."""

    def __call__(
        self, site: AdsorptionSite, adsorbate: Atoms, center: AdsorptionCenter
    ) -> list[MolecularOrientation]:
        """Protocol adherents should implement this function."""


class Transformer(OrientationFactory):
    r"""A :class:`~ccu.structure.symmetry.Transformation`\ -based :class:`OrientationFactory`.

    Instances of this class generate
    :class:`MolecularOrientations <ccu.structure.geometry.MolecularOrientation>` by
    transforming each :class:`~ccu.adsorption.sites.SiteAlignment`
    :class:`~ccu.structure.symmetry.Transformation`.

    Attributes:
        transformations: A list of
            :class:`~ccu.structure.symmetry.Transformation` instances.
        check_symmetry: Whether or not to exlude symmetric images.

    Note:
        In order for
        :class:`MolecularOrientations <ccu.structure.geometry.MolecularOrientation>`
        representing the original
        :attr:`SiteAlignment.directions <ccu.adsorption.sites.SiteAlignment.direction>` to be
        returned by the :class:`Transformer`, at least one
        :class:`~ccu.structure.symmetry.Transformation`
        in :attr:`!Transformer.transformations` should be equivalent to
        the identity transformation.
    """

    def __init__(
        self,
        transformations: Iterable[Transformation] | None = None,
        check_symmetry: bool = False,
    ) -> None:
        """Instantiate a :class:`Transformer`.

        Args:
            transformations: A list of
                :class:`~ccu.structure.symmetry.Transformation` instances.
                Defaults to a list containing a single
                :class:`~ccu.structure.symmetry.Transformation` that returns a
                copy of the input :class:~ase.Atoms` object.
            check_symmetry: Whether or not to exlude symmetric images.
        """
        self.transformations = list(transformations or [lambda a: a.copy()])
        self.check_symmetry = check_symmetry

    def __call__(
        self, site: AdsorptionSite, adsorbate: Atoms, center: AdsorptionCenter
    ) -> list[MolecularOrientation]:
        """Generate orientations for each transformation and site alignment."""
        orientations: list[MolecularOrientation] = []
        structures: list[Atoms] = []

        for i, alignment in enumerate(site.alignments):
            site_aligned = align(
                adsorbate,
                (alignment.direction, site.norm),
                center.position,
            )
            for j, transform in enumerate(self.transformations):
                transformed = transform(site_aligned)

                if self.check_symmetry and any(
                    Comparator.check_similarity(s, transformed)
                    for s in structures
                ):
                    continue

                description = f"{alignment.description or i} {j}"
                ax1, ax2, _ = get_axes(transformed)
                orientation = MolecularOrientation((ax1, ax2), description)
                orientations.append(orientation)
                structures.append(transformed)
        return orientations


class OctahedralFactory(Transformer):
    """A :class:`Transformer` composed of the O:sub:`h` symmetry group."""

    def __init__(
        self,
        transformations: Iterable[Transformation] | None = None,
        check_symmetry: bool = False,
    ) -> None:
        """Instantiate a :class:`OctahedralFactory`.

        Args:
            transformations: A list of
                :class:`~ccu.structure.symmetry.Transformation` instances.
                **This argument will be ignored.**
            check_symmetry: Whether or not to exlude symmetric images.
        """
        transformations = [
            *(Rotation(90 * i) for i in range(4)),
            *(Reflection(norm=n) for n in np.identity(3)),
        ]
        self.check_symmetry = check_symmetry
        super().__init__(transformations, check_symmetry)
