from itertools import combinations

from ase.atoms import Atoms
import numpy as np
import pytest

from ccu.adsorption.sites import HUB_TAG
from ccu.adsorption.sites import SITE_TAG
from ccu.adsorption.sites import SPOKE_TAG
from ccu.adsorption.sites import AdsorptionSite
from ccu.adsorption.sites import HubSpokeFinder
from ccu.adsorption.sites import SiteFinder
from ccu.adsorption.sites import Triangulator


@pytest.fixture(name="ignore_identical_sites", params=[True, False])
def fixture_ignore_identical_sites(request: pytest.FixtureRequest) -> bool:
    return bool(request.param)


@pytest.fixture(name="ignore_identical_spokes", params=[True, False])
def fixture_ignore_identical_spokes(request: pytest.FixtureRequest) -> bool:
    return bool(request.param)


class TestHubSpokeFinder:
    @staticmethod
    @pytest.fixture(name="site_finder")
    def fixture_site_finder(
        ignore_identical_spokes: bool,
        tag_structure: None,  # noqa: ARG004
    ) -> SiteFinder:
        return HubSpokeFinder(ignore_identical_spokes)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_spokes", [False])
    def test_should_create_sites_on_all_correctly_tagged_atoms_if_ignore_identical_spokes_is_false(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        tagged_atom_positions = [
            a.position for a in structure if a.tag in (HUB_TAG, SPOKE_TAG)
        ]
        tagged_atoms_represented: list[bool] = []
        for pos in tagged_atom_positions:
            tagged_atoms_represented.append(
                any((site.position == pos).all() for site in sites)
            )
        assert all(tagged_atoms_represented)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_spokes", [False])
    def test_should_create_hub_sites_with_twice_as_many_alignments_as_spoke_sites_when_ignore_identical_spokes_is_false(
        sites: list[AdsorptionSite],
    ) -> None:
        hub_site = sites[-1]
        num_spoke_sites = len(sites) - 1
        assert len(hub_site.alignments) == 2 * num_spoke_sites

    @staticmethod
    def test_should_create_spoke_sites_with_two_alignments(
        sites: list[AdsorptionSite],
    ) -> None:
        spoke_sites_have_two_alignments = []
        for site in sites[:-1]:
            spoke_sites_have_two_alignments.append(len(site.alignments) == 2)
        assert all(spoke_sites_have_two_alignments)

    @staticmethod
    def test_should_raise_error_if_no_hub_atoms_tagged(
        structure: Atoms, ignore_identical_spokes: bool
    ) -> None:
        finder = HubSpokeFinder(ignore_identical_spokes)
        with pytest.raises(
            ValueError, match="There aren't enough atoms with tag"
        ):
            _ = finder(structure)

    @staticmethod
    def test_should_raise_error_if_less_than_two_spoke_atoms_tagged(
        structure: Atoms, ignore_identical_spokes: bool
    ) -> None:
        structure[0].tag = HUB_TAG
        finder = HubSpokeFinder(ignore_identical_spokes)
        with pytest.raises(
            ValueError, match="There aren't enough atoms with tag"
        ):
            _ = finder(structure)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_spokes", [True])
    def test_should_not_create_duplicate_spoke_sites_when_ignore_identical_spokes_is_true(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        symbols = set()
        for site in sites:
            symbol = next(
                a.symbol
                for a in structure
                if (a.position == site.position).all()
            )
            symbols.add(symbol)
        assert len(symbols) == 1

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_spokes", [False])
    def test_should_create_one_more_site_than_number_of_spoke_atoms_when_ignore_identical_spokes_is_false(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        num_spoke_atoms = len([a for a in structure if a.tag == SPOKE_TAG])
        assert len(sites) == (num_spoke_atoms + 1)

    @staticmethod
    def test_should_create_spoke_sites_with_parallel_and_perpendicular_alignments(
        sites: list[AdsorptionSite],
    ) -> None:
        spoke_sites_have_perpendicular_alignments = []
        for site in sites:
            spoke_sites_have_perpendicular_alignments.append(
                site.alignments[0].direction @ site.alignments[1].direction
                == 0.0
            )
        assert all(spoke_sites_have_perpendicular_alignments)


class TestTriangulator:
    @staticmethod
    @pytest.fixture(name="tag_structure")
    def fixture_tag_structure(structure: Atoms) -> None:
        tags = [0] * len(structure)
        tags[0] = tags[1] = tags[3] = SITE_TAG
        structure.set_tags(tags)

    @staticmethod
    @pytest.fixture(name="site_finder")
    def fixture_site_finder(
        ignore_identical_sites: bool,
        tag_structure: None,  # noqa: ARG004
    ) -> SiteFinder:
        return Triangulator(ignore_identical_sites)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_sites", [False])
    def test_should_create_sites_on_all_correctly_tagged_atoms_when_ignore_identical_sites_is_false(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        tagged_atom_positions = [
            a.position for a in structure if a.tag == SITE_TAG
        ]
        tagged_atoms_represented: list[bool] = []
        for pos in tagged_atom_positions:
            tagged_atoms_represented.append(
                any((site.position == pos).all() for site in sites)
            )
        assert all(tagged_atoms_represented)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_sites", [False])
    def test_should_create_in_between_sites(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        tagged_atoms = [a for a in structure if a.tag == SITE_TAG]
        in_between_sites = list(combinations(tagged_atoms, r=2))
        site_positions = [site.position for site in sites]
        in_between_sites_present = []

        for site1, site2 in in_between_sites:
            in_between_site = (site1.position + site2.position) / 2
            in_between_sites_present.append(
                any((pos == in_between_site).all() for pos in site_positions)
            )

        assert all(in_between_sites_present)

    @staticmethod
    def test_should_create_centroid_site(
        sites: list[AdsorptionSite], structure: Atoms
    ) -> None:
        tagged_atoms = [a for a in structure if a.tag == SITE_TAG]
        centroid_site = np.mean([a.position for a in tagged_atoms], axis=0)
        site_positions = [site.position for site in sites]
        assert any((site == centroid_site).all() for site in site_positions)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_sites", [False])
    def test_should_create_alignments_for_all_vertices_if_ignore_identical_sites_is_false(
        sites: list[AdsorptionSite],
    ) -> None:
        assert all(len(site.alignments) == 3 for site in sites)

    @staticmethod
    @pytest.mark.parametrize("ignore_identical_sites", [True])
    def test_should_find_three_sites_on_a_single_element_surface_if_ignore_identical_sites_is_true(
        sites: list[AdsorptionSite],
    ) -> None:
        assert len(sites) == 3

    @staticmethod
    def test_should_raise_error_if_less_than_three_atoms_tagged(
        ignore_identical_sites: bool, structure: Atoms
    ) -> None:
        structure.set_tags([0] * len(structure))
        finder = Triangulator(ignore_identical_sites)
        with pytest.raises(
            ValueError, match="There must be at least three atoms with tag"
        ):
            _ = finder(structure)

    @staticmethod
    def test_should_raise_warning_if_more_than_three_atoms_tagged(
        ignore_identical_sites: bool, structure: Atoms
    ) -> None:
        structure.set_tags([SITE_TAG] * len(structure))
        finder = Triangulator(ignore_identical_sites)
        with pytest.raises(
            UserWarning, match="More than three atoms tagged with tag"
        ):
            _ = finder(structure)
