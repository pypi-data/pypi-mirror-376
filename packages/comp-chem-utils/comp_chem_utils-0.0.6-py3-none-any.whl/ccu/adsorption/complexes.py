"""Generate adsorbate complexes.

Specifically, this module defines the :class:`AdsorbateComplexFactory` class
which combines the functionalities of the
:class:`~ccu.adsorption.sites.SiteFinder`,
:class:`~ccu.adsorption.orientation.OrientationFactory`, and
:class:`~ccu.adsorption.orientation.CenterFactory` classes to generate
adsorbate complexes.

Examples:
    1. A simplified interface to
       :class:`~ccu.adsorption.complexes.AdsorbateComplexFactory`
       using :func:`generate_complexes`.

    >>> import numpy as np
    >>> from ase.atoms import Atoms
    >>> from ase.build import fcc100
    >>> from ccu.adsorption.complexes import generate_complexes
    >>> from ccu.adsorption.sites import AdsorptionSite, SiteAlignment
    ... # Create a 3 x 3 x 1 Cu(100) surface
    >>> cu100 = fcc100("Cu", (3, 3, 1))
    ... # "Dope" the surface with Ag
    >>> cu100.set_chemical_symbols(
    ...     [(a.symbol if a.index % 2 == 0 else "Ag") for a in cu100]
    ... )
    >>> cu100.center(vacuum=10, axis=2)
    >>> # This site-finder always returns an adsorption site on the first atom
    >>> def finder(structure: Atoms) -> list[AdsorptionSite]:
    ...     return [
    ...         AdsorptionSite(
    ...             position=structure[0].position,
    ...             description=f"on {structure[0].symbol}",
    ...             alignments=[SiteAlignment(np.array([1.0, 0.0, 0.0]), "x")],
    ...             norm=np.array([0, 0.0, 1.0]),
    ...         )
    ...     ]
    >>> complexes = generate_complexes(
    ...     structure=cu100,
    ...     adsorbate="H",
    ...     finder=finder,
    ...     symmetry=True,
    ... )
    >>> len(complexes)
    1

    2. Fine-tuned control over all aspects of adsorbate complex generation
       using :class:`~ccu.adsorption.complexes.AdsorbateComplexFactory`.

    >>> from ase.build import fcc100
    >>> from ccu.adsorption.adsorbates import get_adsorbate
    >>> from ccu.adsorption.complexes import AdsorbateComplexFactory
    >>> from ccu.adsorption.orientation import Transformer, atomic_centerer
    >>> from ccu.adsorption.sites import HubSpokeFinder, HUB_TAG, SPOKE_TAG
    >>> from ccu.structure.symmetry import Rotation
    ... # Create a 3 x 3 x 1 Cu(100) surface
    >>> cu100 = fcc100("Cu", (3, 3, 1))
    >>> tags = [0] * len(cu100)
    ... # Tag hub and spoke atoms
    >>> tags[4] = HUB_TAG
    >>> tags[1] = tags[3] = tags[5] = tags[7] = SPOKE_TAG
    >>> cu100.set_tags(tags)
    ... # Create two adsorbate orientations per site alignment
    >>> transformer = Transformer([Rotation(0), Rotation(180)])
    >>> factory = AdsorbateComplexFactory(
    ...     site_finder=HubSpokeFinder(),
    ...     orientation_factory=transformer,
    ...     # Create adsorbate complexes centered on each atom in adsorbate
    ...     center_factory=atomic_centerer,
    ...     # Reduce minimum surface-adsorbate separation to 1.5 Angstroms
    ...     separation=1.5,
    ...     # Tag all adsorbate atoms with -50
    ...     adsorbate_tag=-50,
    ... )
    >>> co2 = get_adsorbate("CO2")
    >>> complexes = factory.get_complexes(cu100, co2)
    >>> len(complexes)
    24
"""

from pathlib import Path
from typing import Literal

from ase.atoms import Atoms
from ase.io import read

from ccu.adsorption import adsorbates
from ccu.adsorption.orientation import CenterFactory
from ccu.adsorption.orientation import OctahedralFactory
from ccu.adsorption.orientation import OrientationFactory
from ccu.adsorption.orientation import Transformer
from ccu.adsorption.orientation import atomic_centerer
from ccu.adsorption.orientation import com_centerer
from ccu.adsorption.orientation import special_centerer
from ccu.adsorption.sites import AdsorptionSite
from ccu.adsorption.sites import SiteFinder
from ccu.adsorption.sites import Triangulator
from ccu.structure import geometry
from ccu.structure.geometry import align

#: The default tag to use for adsorbates when creating adsorbate complexes
DEFAULT_ADSORBATE_TAG = -99


class AdsorbateComplexFactory:
    r"""Generate adsorption complexes from structures and adsorbates.

    Given an adsorbate and a structure, an `AdsorbateComplexFactory`
    generates all adsorption complexes on all sites of all orientations,
    alignments, and centers.

    Attributes:
        site_finder: A callable that accepts an :class:`~ase.Atoms` object
            and returns an iterable of sites on the structure.
        orientation_factory: An
            :class:`~ccu.adsorption.orientation.OrientationFactory`
            responsible for generating
            :class:`MolecularOrientations <ccu.structure.geometry.MolecularOrientation>`
            from :class:`AdsorptionSites <ccu.adsorption.sites.AdsorptionSite>` and
            an adsorbate.
        center_factory: A :class:`~ccu.adsorption.orientation.CenterFactory`
            that will generate displacements from adsorbates.
        separation: The distance (in Angstroms) that the adsorbate should
            be placed from the surface.
        adsorbate_tag: An integer to be used to tag adsorbate atoms in
            adsorbate complexes.
    """

    def __init__(
        self,
        site_finder: SiteFinder,
        orientation_factory: OrientationFactory | None = None,
        center_factory: CenterFactory | None = None,
        separation: float = 1.8,
        adsorbate_tag: int = DEFAULT_ADSORBATE_TAG,
    ) -> None:
        r"""Create an `AdsorbateComplexFactory`.

        Args:
            site_finder: A callable that accepts an :class:`~ase.Atoms` object
                and returns an iterable of sites on the structure.
            orientation_factory: An
                :class:`~ccu.adsorption.orientation.OrientationFactory`
                responsible for generating
                :class:`AdsorbateOrientations <ccu.structure.geometry.MolecularOrientation>`
                from :class:`AdsorptionSites <ccu.adsorption.sites.AdsorptionSite>`,
                :class:`AdsorptionCenters <ccu.adsorption.orientation.AdsorptionCenter>`,
                and adsorbates. The default will align adsorbates to site
                aligments using their primary axis.
            center_factory: A :class:`~ccu.adsorption.orientation.CenterFactory`
                that will generate displacements from adsorbates. The default
                will place adsorbates using their center-of-mass.
            separation: The distance (in Angstroms) that the adsorbate should
                be placed from the surface. Defaults to 1.8.
            adsorbate_tag: An integer to be used to tag adsorbate atoms in
                adsorbate complexes. Defaults to :data:`DEFAULT_ADSORBATE_TAG`.
        """
        self.site_finder = site_finder
        self.orientation_factory = orientation_factory or Transformer()
        self.center_factory = center_factory or com_centerer
        self.separation = separation
        self.adsorbate_tag = adsorbate_tag

    def get_complexes(self, structure: Atoms, adsorbate: Atoms) -> list[Atoms]:
        """Generate adsorbate-surface complexes on a given site.

        Args:
            structure: An :class:`~ase.Atoms` object representing the
                structure.
            adsorbate: An :class:`~ase.Atoms` object representing the
                adsorbate.

        Returns:
            A list of adsorption complexes for the site.
        """
        complexes: list[Atoms] = []

        for site in self.site_finder(structure):
            for center in self.center_factory(adsorbate):
                for orientation in self.orientation_factory(
                    site, adsorbate, center
                ):
                    oriented = align(
                        adsorbate=adsorbate,
                        directions=orientation.directions,
                        center=center.position,
                    )
                    oriented.positions -= center.position

                    # Tags to distinguish adsorbate from surface atoms (useful for
                    # vibrational calculations)
                    oriented.set_tags(self.adsorbate_tag)
                    oriented.set_cell(structure.cell[:])
                    self.place_adsorbate(
                        structure,
                        oriented,
                        site,
                    )

                    # Add adsorbate to structure
                    adsorbate_complex = structure.copy()
                    adsorbate_complex.extend(oriented)
                    structure_metadata = {
                        "adsorbate": oriented.info.get(
                            "structure", str(oriented.symbols)
                        ),
                        "site": site.description,
                        "orientation": orientation.description,
                        "center": center.description,
                    }
                    adsorbate_complex.info.update(structure_metadata)
                    complexes.append(adsorbate_complex)

        return complexes

    def place_adsorbate(
        self,
        structure: Atoms,
        adsorbate: Atoms,
        site: AdsorptionSite,
    ) -> None:
        """Center an adsorbate onto a site using the adsorbate origin.

        The adsorbate is placed on the specified site while respecting the
        minimum specified separation.

        Args:
            structure: An :class:`~ase.Atoms` instance representing
                the structure on which to place the adsorbate.
            adsorbate: An :class:`~ase.Atoms` instance representing
                the adsorbate to be placed.
            site: An :class:`~ccu.adsorption.sites.AdsorptionSite` instance
                representing the site on which the adsorbate is to be placed.
        """
        adsorbate.positions += site.position
        separation = geometry.calculate_separation(adsorbate, structure)

        # TODO: add check if adsorbate moved out of cell and throw error
        while separation < self.separation:
            adsorbate.positions += 0.1 * site.norm
            separation = geometry.calculate_separation(adsorbate, structure)


def _get_structure_with_name(
    structure: str | Path, *, preserve_info: bool = False
) -> Atoms:
    """Load an :class:`~ase.Atoms` object from a file and stores filename.

    The plain text description is stored in the ``info`` dictionary of the
    structure under the key ``"structure"`` and can be accessed as follows::

        atoms = _get_structure_with_name(structure)
        structure_description = atoms.info["structure"]

    Args:
        structure: The path to the structure to be loaded. Note that if loading
            the structure returns more than one structure, the last structure
            will be loaded.
        preserve_info: Whether or not to preserve the structure information in
            the info dictionary. If False, the ``"structure"`` key will be
            overriden if set. Defaults to False.

    Returns:
        The loaded :class:`~ase.Atoms` object.
    """
    structure = Path(structure)
    atoms = read(structure)
    atoms = atoms[-1] if isinstance(atoms, list) else atoms
    if not preserve_info or "structure" not in atoms.info:
        atoms.info["structure"] = structure.stem

    return atoms


def generate_complexes(
    adsorbate: str | Path | Atoms,
    structure: str | Path | Atoms,
    *,
    separation: float = 1.8,
    centers: Literal["com", "special", "all"] = "com",
    symmetry: bool = False,
    finder: SiteFinder | None = None,
    adsorbate_tag: int = DEFAULT_ADSORBATE_TAG,
) -> list[Atoms]:
    r"""A convenience wrapper around :meth:`AdsorbateComplexFactory.get_complexes`.

    Args:
        adsorbate: The adsorbate to place on `structure`. This can be passed
            as a string, path, or :class:`~ase.Atoms` object. If passed
            as a string, the string will be used to retrieve the corresponding
            adsorbate using :func:`ccu.adsorption.adsorbates.get_adsorbate`.
            If passed as a path, an :class:`~ase.Atoms` object will be read
            from the associated file. If passed as an :class:`~ase.Atoms` object,
            then the `"structure"` key of `adsorbate.info` must map to a
            string.
        structure: The structure on which `adsorbate` is to be be placed.
            If passed as a string or path, the structure will be read from
            the indicated file. If passed as an :class:`~ase.Atoms` object,
            then the `"structure"` key of `structure.info` must map to a str.
        separation: A float indicating how far (in Angstroms) the adsorbate
            should be placed from the surface. Defaults to 1.8.
        centers: A string indicating what kind of centers will be used to place
            `adsorbate`. `"com"` indicates that `adsorbate` will be placed
            using its center-of-mass. `"special"` indicates that the atoms
            indicated by the `"special_centers"` key in `adsorbate.info`.
            `"all"` indicates that all atomic centers will be used.
        symmetry: A bool indicating whether or not the symmetry of the
            adsorbate is to be considered when generating complexes. Defaults
            to False.
        finder: A callable that accepts an :class:`~ase.Atoms` object and
            returns an iterable of sites on the structure. Defaults to
            `Triangulator()`.
        adsorbate_tag: The tag to give to adsorbate atoms. Defaults to
            :data:`DEFAULT_ADSORBATE_TAG`.

    Returns:
        A list of :class:`~ase.Atoms` objects representing adsorption
        complexes.

    .. seealso:: :class:`ccu.adsorption.sites.HubSpokeFinder`, :meth:`AdsorbateComplexFactory.get_complexes`
    """
    if isinstance(adsorbate, str):
        adsorbate = adsorbates.get_adsorbate(adsorbate)
    elif isinstance(adsorbate, Path):
        adsorbate = _get_structure_with_name(adsorbate)

    if isinstance(structure, str | Path):
        structure = _get_structure_with_name(structure)

    match centers:
        case "all":
            center_factory = atomic_centerer
        case "special":
            center_factory = special_centerer
        case _:
            center_factory = com_centerer

    factory = AdsorbateComplexFactory(
        site_finder=finder if finder else Triangulator(),
        orientation_factory=OctahedralFactory(check_symmetry=symmetry),
        center_factory=center_factory,
        separation=separation,
        adsorbate_tag=adsorbate_tag,
    )
    return factory.get_complexes(structure, adsorbate)


def write_complexes(complexes: list[Atoms], dir_name: Path) -> list[Path]:
    """A utility function for automatically saving adsorption complexes.

    Adsorption complexes are saved with the generic format:

    `structure_adsorbate_site_center_orientation__N.traj`

    The "structure", "adsorbate", "site", "center", and "orientation"
    components are derived from the corresponding values in
    :attr:`!Atoms.info`. `N` is a zero-indexed label that is incremented so as
    to avoid filename clashes.

    Args:
        complexes: A list of :class:`~ase.Atoms` objects representing complexes,
            such as that created by
            :meth:`.AdsorbateComplexFactory.get_complexes`. In order for the
            trajectory files to be templated correctly, the keys,
            `"structure"`, `"adsorbate"`, and `"site"` must be present in the
            :attr:`!Atoms.info` dictionary of each :class:`~ase.Atoms`
            object in `complexes`. `"orientation"` may optionally be present.
        dir_name: The directory in which to save the complexes.

    Returns:
        The list of files to which the adsorption complexes were written.
    """
    dir_name.mkdir(parents=True, exist_ok=True)
    written_complexes: list[Path] = []

    for complex_to_write in complexes:
        info = complex_to_write.info
        description = [
            info["structure"].replace(" ", "_"),
            info["adsorbate"].replace(" ", "_"),
            info["site"].replace(" ", "_"),
            info["center"].replace(" ", "_"),
            info["orientation"].replace(" ", "_"),
        ]
        stem = "_".join(description)
        index = 0
        filename = Path(dir_name, f"{stem}_{index}.traj")

        while filename.exists():
            index += 1
            filename = Path(dir_name, f"{stem}_{index}.traj")

        complex_to_write.write(filename)
        written_complexes.append(filename)

    return written_complexes
