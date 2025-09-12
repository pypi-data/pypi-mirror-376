"""Find and distinguish adsorption sites.

This module defines the :class:`AdsorptionSite` named tuple
which represents an adsorption site as a point in space characterized by a
surface norm, description, and a set of alignments (represented by the
:class:`SiteAlignment` class). In addition, this module defines the
:class:`SiteFinder` protocol and the :class:`HubSpokeFinder` and
:class:`Triangulator` classes whose instances implement this protocol.

Example:
    >>> from ase.build import fcc100
    >>> from ccu.adsorption.sites import HubSpokeFinder, HUB_TAG, SPOKE_TAG
    ... # Construct a surface
    >>> cu100 = fcc100("Cu", (3, 3, 1))
    ... # Tag the hub-and-spoke atoms appropriately
    >>> tags = [0] * len(cu100)
    >>> tags[1] = tags[3] = SPOKE_TAG
    >>> tags[4] = HUB_TAG
    >>> cu100.set_tags(tags)
    >>> finder = HubSpokeFinder()
    >>> sites = finder(cu100)
    ... # This first site is on the first spoke
    >>> (sites[0].position == cu100[1].position).all()
    True
"""

from itertools import combinations
from typing import TYPE_CHECKING
from typing import Literal
from typing import NamedTuple
from typing import Protocol
import warnings

from ase.atoms import Atoms
import numpy as np

from ccu.structure.geometry import calculate_norm

if TYPE_CHECKING:
    from numpy.typing import NDArray


class SiteAlignment(NamedTuple):
    """An alignment that an adsorbate can assume on a site.

    Attributes:
        direction: A length 3, 1D :class:`numpy.ndarray` of floats representing a
            direction in space.
        description: A description of the site alignment.

    """

    direction: "NDArray[np.floating]"
    description: str


class AdsorptionSite(NamedTuple):
    """An adsorption site.

    Attributes:
        position: A length 3, 1D :class:`numpy.ndarray` representing the location of
            the adsorption site.
        description: A description of the adsorption site as a string.
        alignments: A list of :class:`SiteAlignment` objects defining
            alignments for the site.
        norm: A length 3, 1D :class:`numpy.ndarray` representing the unit
            normal vector for the surface hosting the adsorption site.

    """

    position: "NDArray[np.floating]"
    description: str
    alignments: list[SiteAlignment]
    norm: "NDArray[np.floating]"


class SiteFinder(Protocol):
    """A protocol for finding adsorption sites."""

    def __call__(self, structure: Atoms) -> list[AdsorptionSite]:
        """Return a list of a structure's adsorption sites."""


#: The default tag used to identify spoke atoms in
#: :class:`HubSpokeFinders <HubSpokeFinder>`
SPOKE_TAG = -1

#: The default tag used to identify the hub atom in
#: :class:`HubSpokeFinders <HubSpokeFinder>`
HUB_TAG = -2


class HubSpokeFinder(SiteFinder):
    """A :class:`SiteFinder` that finds sites in a hub-and-spoke fashion.

    The hub-and-spoke model describes a set of adsorption sites on a structure.
    The "hub" is comprised of one atom, and the "spokes" are imaginary lines
    drawn from the hub to other atoms in the structure.

    Attributes:
        ignore_identical_spokes: Whether or not to restrict the returned sites
            to ignore those "spoke" sites on atoms of the same chemical symbol.
        norm_convention: The convention with which to define normal vectors as
            outwards or inwards from the surface. The choices of `"up"` and
            `"down"` correspond to setting `reverse=False` and `reverse=True`
            in :func:`~ccu.structure.geometry.calculate_norm`.
        spoke_tag: The tag designating spoke atoms.
        hub_tag: The tag designating hub atoms.

    .. seealso:: :func:`~ccu.structure.geometry.calculate_norm`
    """

    def __init__(
        self,
        ignore_identical_spokes: bool = True,
        norm_convention: Literal["up", "down"] = "up",
        spoke_tag: int = SPOKE_TAG,
        hub_tag: int = HUB_TAG,
    ) -> None:
        """Construct a :class:`HubSpokeFinder`.

        Args:
            ignore_identical_spokes: Whether or not to restrict the returned
                sites to ignore those "spoke" sites on atoms of the same
                chemical symbol.
            norm_convention: The convention with which to define normal vectors
                as outwards or inwards from the surface. The choices of `"up"`
                and `"down"` correspond to setting `reverse=False` and
                `reverse=True` in :func:`~ccu.structure.geometry.calculate_norm`.
            spoke_tag: The tag designating spoke atoms. Defaults to
                :data:`SPOKE_TAG`.
            hub_tag: The tag designating hub atoms. Defaults to
                :data:`HUB_TAG`.
        """
        self.ignore_identical_spokes = ignore_identical_spokes
        self.norm_convention = norm_convention
        self.spoke_tag = spoke_tag
        self.hub_tag = hub_tag

    def __call__(self, structure: Atoms) -> list[AdsorptionSite]:
        """Find sites on a structure according to a hub-and-spoke model.

        Args:
            structure: An :class:`~ase.Atoms` object in which at least two atoms
                have tags equal to `self.spoke_tag` and at least one atom has a
                tag equal to `self.hub_tag`. To avoid unexpected behaviour, only
                one atom should have the tag equal to `self.hub_tag`.

        Returns:
            A list of :class:`AdsorptionSite` instances.

        Raises:
            ValueError: There aren't enough atoms with tags equal to
            `self.spoke_tag` or `self.hub_tag`.
        """
        spokes = [atom for atom in structure if atom.tag == self.spoke_tag]

        try:
            hub = next(atom for atom in structure if atom.tag == self.hub_tag)
        except StopIteration as err:
            msg = (
                f"There aren't enough atoms with tag=self.hub_tag "
                f"({self.hub_tag})"
            )
            raise ValueError(msg) from err

        # Can't calculate cross-product (required to calculate norm) with only
        # one vector
        if len(spokes) < 2:  # noqa: PLR2004
            msg = (
                "There aren't enough atoms with tag=self.spoke_tag "
                f"({self.spoke_tag})"
            )
            raise ValueError(msg)

        surface_norm = calculate_norm(
            [a.position for a in [*spokes, hub]],
            reverse=self.norm_convention == "down",
        )

        if self.ignore_identical_spokes:
            # Reversal ensures lower index spokes are preferred for a given symbol
            spokes = list({a.symbol: a for a in reversed(spokes)}.values())

        sites: list[AdsorptionSite] = []
        spoke_alignments: list[SiteAlignment] = []

        for _, spoke in enumerate(spokes):
            vec = spoke.position - hub.position
            parallel = SiteAlignment(
                vec, f"parallel to spoke {spoke.symbol} {spoke.index}"
            )
            perp_direction = np.cross(vec, surface_norm)
            perp_direction /= np.linalg.norm(perp_direction)
            perpendicular = SiteAlignment(
                perp_direction,
                f"perpendicular to spoke {spoke.symbol} {spoke.index}",
            )
            spoke_site = AdsorptionSite(
                spoke.position,
                f"{spoke.symbol} {spoke.index} ontop",
                [parallel, perpendicular],
                surface_norm,
            )
            sites.append(spoke_site)
            spoke_alignments.extend([parallel, perpendicular])

        hub_site = AdsorptionSite(
            hub.position,
            f"{hub.symbol} {hub.index} ontop",
            spoke_alignments,
            surface_norm,
        )
        sites.append(hub_site)

        return sites


#: The default tag used to identify site atoms in
#: :class:`Triangulators <Triangulator>`
SITE_TAG = -1


class Triangulator(SiteFinder):
    """A :class:`SiteFinder` that triangulates sites.

    A :class:`Triangulator` finds sites at the vertices, midpoints, and
    centroid of a triangle.

    Attributes:
        ignore_identical_sites: Whether or not to restrict the returned sites
            to ignore those sites on atoms of the same chemical symbol.
        norm_convention: The convention with which to define normal vectors as
            outwards or inwards from the surface. The choices of `"up"` and
            `"down"` correspond to setting `reverse=False` and `reverse=True`
            in :func:`~ccu.structure.geometry.calculate_norm`.
        site_tag: The tag designating site atoms.

    .. seealso:: :func:`~ccu.structure.geometry.calculate_norm`
    """

    def __init__(
        self,
        ignore_identical_sites: bool = True,
        norm_convention: Literal["up", "down"] = "up",
        site_tag: int = SITE_TAG,
    ) -> None:
        """Construct a :class:`HubSpokeFinder`.

        Args:
            ignore_identical_sites: Whether or not to restrict the returned
                sites to ignore those sites on atoms of the same chemical
                symbol.
            norm_convention: The convention with which to define normal vectors
                as outwards or inwards from the surface. The choices of `"up"`
                and `"down"` correspond to setting `reverse=False` and
                `reverse=True` in :func:`~ccu.structure.geometry.calculate_norm`.
            site_tag: The tag designating site atoms. Defaults to
                :data:`SITE_TAG`.
        """
        self.ignore_identical_sites = ignore_identical_sites
        self.norm_convention = norm_convention
        self.site_tag = site_tag

    def __call__(self, structure: Atoms) -> list[AdsorptionSite]:
        """Triangulate sites on a structure.

        Args:
            structure: An :class:`~ase.Atoms` object in which exactly three
                atoms have tags equal to `self.site_tag`.

        Returns:
            A list of :class:`AdsorptionSite` instances.

        Raises:
            ValueError: There aren't at least three atoms with tags equal to
            `self.site_tag`.
        """
        site_atoms = [atom for atom in structure if atom.tag == self.site_tag]
        if len(site_atoms) < 3:  # noqa: PLR2004
            msg = (
                f"There must be at least three atoms with tag=self.site_tag "
                f"({self.site_tag})"
            )
            raise ValueError(msg)
        elif len(site_atoms) > 3:  # noqa: PLR2004
            msg = (
                "More than three atoms tagged with tag=self.site_tag "
                f"({self.site_tag}). Only the first three atoms will be used "
                "Results may be unexpected"
            )
            warnings.warn(msg, UserWarning, stacklevel=2)

        site_atoms = site_atoms[:4]
        centroid_position = np.mean([a.position for a in site_atoms], axis=0)
        centroid_description = (
            " ".join(f"{a.symbol} {a.index}" for a in site_atoms) + " hollow"
        )
        surface_norm = calculate_norm(
            [a.position for a in site_atoms],
            reverse=self.norm_convention == "down",
        )
        directions = [site_atoms[0].position - site_atoms[1].position]
        pairs = [tuple(site_atoms[:2])]

        if self.ignore_identical_sites:
            # Reversal ensures lower index spokes are preferred for a given symbol
            site_atoms = list(
                {a.symbol: a for a in reversed(site_atoms)}.values()
            )
        if len(site_atoms) > 1:
            directions = [
                x.position - y.position
                for x, y in combinations(site_atoms, r=2)
            ]
            pairs = list(combinations(site_atoms, r=2))

        alignments = [
            SiteAlignment(x / np.linalg.norm(x), str(i))
            for i, x in enumerate(directions)
        ]
        sites: list[AdsorptionSite] = []

        for _, site_atom in enumerate(site_atoms):
            ontop_site = AdsorptionSite(
                site_atom.position,
                f"{site_atom.symbol} {site_atom.index} ontop",
                alignments,
                surface_norm,
            )
            sites.append(ontop_site)

        for site1, site2 in pairs:
            bridge_site = AdsorptionSite(
                (site1.position + site2.position) / 2,
                f"{site1.symbol} {site1.index} "
                f"{site2.symbol} {site2.index} bridge ",
                alignments,
                surface_norm,
            )
            sites.append(bridge_site)

        hollow_site = AdsorptionSite(
            centroid_position,
            centroid_description,
            alignments,
            surface_norm,
        )
        sites.append(hollow_site)

        return sites
