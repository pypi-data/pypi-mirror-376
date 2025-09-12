from pathlib import Path

from ase.atoms import Atoms
import numpy as np
import pytest

from ccu.adsorption.complexes import AdsorbateComplexFactory
from ccu.adsorption.complexes import generate_complexes
from ccu.adsorption.complexes import write_complexes
from ccu.adsorption.orientation import CenterFactory
from ccu.adsorption.orientation import OrientationFactory
from ccu.adsorption.orientation import Transformer
from ccu.adsorption.orientation import com_centerer
from ccu.adsorption.sites import SITE_TAG
from ccu.adsorption.sites import AdsorptionSite
from ccu.adsorption.sites import SiteFinder
from ccu.structure.axisfinder import get_axes


@pytest.fixture(name="orientation_factory")
def fixture_orientation_factory() -> OrientationFactory:
    return Transformer()


@pytest.fixture(name="center_factory")
def fixture_center_factory() -> CenterFactory:
    return com_centerer


@pytest.fixture(name="separation")
def fixture_separation() -> float:
    return 1.0


@pytest.fixture(name="adsorbate_tag")
def fixture_adsorbate_tag() -> int:
    return -99


@pytest.fixture(name="complex_factory")
def fixture_complex_factory(
    site_finder: SiteFinder,
    orientation_factory: OrientationFactory,
    center_factory: CenterFactory,
    separation: float,
    adsorbate_tag: int,
) -> AdsorbateComplexFactory:
    return AdsorbateComplexFactory(
        site_finder=site_finder,
        orientation_factory=orientation_factory,
        center_factory=center_factory,
        separation=separation,
        adsorbate_tag=adsorbate_tag,
    )


@pytest.fixture(name="complexes")
def fixture_complexes(
    structure: Atoms,
    adsorbate: Atoms,
    complex_factory: AdsorbateComplexFactory,
) -> list[Atoms]:
    return complex_factory.get_complexes(structure, adsorbate)


class TestPlaceAdsorbate:
    @staticmethod
    @pytest.mark.parametrize("adsorbate", ["H", "C", "O", "N"], indirect=True)
    def test_should_place_adsorbate_with_center_at_least_separation_away(
        complexes: list[Atoms],
        adsorbate: Atoms,
        sites: list[AdsorptionSite],
        separation: float,
    ) -> None:
        centers_are_exactly_placed_for_monoatomic_adsorbates = []
        position = sites[0].position
        for c in complexes:
            adsorbate_subset = c[-len(adsorbate) :]
            com = adsorbate_subset.get_center_of_mass()
            distance = np.linalg.norm(com - position)
            centers_are_exactly_placed_for_monoatomic_adsorbates.append(
                distance >= separation
            )
        assert all(centers_are_exactly_placed_for_monoatomic_adsorbates)


class TestGetComplexes:
    @staticmethod
    def test_should_get_complexes(
        complexes: list[Atoms],
    ) -> None:
        assert complexes

    @staticmethod
    def test_should_tag_adsorbate_atoms_with_correct_tag(
        adsorbate_tag: int, complexes: list[Atoms], adsorbate: Atoms
    ) -> None:
        complexes_have_adsorbates_tagged = []
        for c in complexes:
            complexes_have_adsorbates_tagged.append(
                (c[-len(adsorbate) :].get_tags() == adsorbate_tag).all()
            )
        assert all(complexes_have_adsorbates_tagged)

    @staticmethod
    def test_should_create_adsorbate_complexes_with_aligned_adsorbates(
        complexes: list[Atoms],
        adsorbate: Atoms,
        sites: list[AdsorptionSite],
    ) -> None:
        complexes_are_aligned_with_primary_axis = []
        alignment = sites[0].alignments[0].direction
        for c in complexes:
            adsorbate_subset = c[-len(adsorbate) :]
            axis, *_ = get_axes(adsorbate_subset)
            complexes_are_aligned_with_primary_axis.append(
                np.linalg.norm(np.cross(alignment, axis) == 0.0)
            )
        assert all(complexes_are_aligned_with_primary_axis)


class TestGenerateComplexes:
    @staticmethod
    @pytest.fixture(name="tag_structure")
    def fixture_tag_structure(structure: Atoms) -> None:
        tags = [0] * len(structure)
        tags[1] = tags[3] = tags[4] = SITE_TAG
        structure.set_tags(tags)

    @staticmethod
    def test_should_generate_complexes(
        structure: Atoms,
        adsorbate: Atoms,
        separation: float,
        tag_structure: None,  # noqa: ARG004
    ) -> None:
        generated_complexes = generate_complexes(
            structure=structure,
            adsorbate=adsorbate,
            separation=separation,
            centers="com",
        )
        assert generated_complexes


class TestWriteComplexes:
    @staticmethod
    def test_should_write_complexes(
        complexes: list[Atoms], tmp_path: Path
    ) -> None:
        files = write_complexes(complexes, tmp_path)
        assert all(file.exists() for file in files)
