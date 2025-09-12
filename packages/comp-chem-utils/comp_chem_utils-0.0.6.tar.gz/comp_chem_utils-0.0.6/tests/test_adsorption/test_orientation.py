from itertools import combinations
from typing import TYPE_CHECKING
from typing import Any

from ase.atoms import Atoms
import numpy as np
import pytest

from ccu.adsorption.orientation import AdsorptionCenter
from ccu.adsorption.orientation import OctahedralFactory
from ccu.adsorption.orientation import Transformer
from ccu.adsorption.sites import AdsorptionSite
from ccu.adsorption.sites import SiteAlignment
from ccu.structure.comparator import Comparator
from ccu.structure.geometry import align
from ccu.structure.symmetry import Rotation
from ccu.structure.symmetry import Transformation

if TYPE_CHECKING:
    from numpy.typing import NDArray


@pytest.fixture(name="alignments")
def fixture_alignments() -> int:
    return 1


@pytest.fixture(name="site_alignments")
def fixture_site_alignments(
    structure: Atoms, alignments: int
) -> list[SiteAlignment]:
    site_alignments: list[SiteAlignment] = []
    for i in range(alignments):
        direction = structure[0].position - structure[i + 1].position
        direction /= np.linalg.norm(direction)
        site_alignment = SiteAlignment(direction, str(i))
        site_alignments.append(site_alignment)
    return site_alignments


@pytest.fixture(name="adsorption_site")
def fixture_adsorption_site(
    structure: Atoms, site_alignments: list[SiteAlignment]
) -> AdsorptionSite:
    return AdsorptionSite(
        structure[0].position,
        "origin",
        site_alignments,
        np.array([0, 0, 1.0]),
    )


@pytest.fixture(name="directions")
def fixture_directions() -> (
    "tuple[NDArray[np.floating], NDArray[np.floating]]"
):
    basis = np.identity(3)
    return basis[0], basis[1]


# The number of rotations in the transformation
@pytest.fixture(name="sym_order")
def fixture_sym_order() -> int:
    return 4


@pytest.fixture(name="transformations")
def fixture_transformations(
    directions: "tuple[NDArray[np.floating], NDArray[np.floating]]",
    sym_order: int,
) -> list[Transformation]:
    axis = np.cross(*directions)
    return [Rotation(90 * (1 + i), axis) for i in range(sym_order)]


@pytest.fixture(name="check_symmetry")
def fixture_check_symmetry() -> bool:
    return False


@pytest.fixture(name="transformer")
def fixture_transformer(
    transformations: list[Transformation], check_symmetry: bool
) -> Transformer:
    return Transformer(transformations, check_symmetry)


# Tolerance for alignment tests
_alignment_tol = 1e-6


def _get_com(a: Atoms) -> AdsorptionCenter:
    return AdsorptionCenter(a.get_center_of_mass(), "COM")


class TestTransformer:
    @staticmethod
    @pytest.mark.parametrize("transformer", [Transformer()])
    @pytest.mark.parametrize("alignments", [2, 3, 4])
    @pytest.mark.parametrize(
        "adsorbate",
        ["H2", "CO", "CO2", "OH", "NHO", "COOH", "CH3", "NH2OH"],
        indirect=True,
    )
    def test_should_only_return_aligned_orientations_with_identity_transformer(
        adsorbate: Atoms,
        adsorption_site: AdsorptionSite,
        transformer: Transformer,
    ):
        def _aligned(
            directions1: "tuple[NDArray[np.floating], NDArray[np.floating]]",
            directions2: "tuple[NDArray[np.floating], NDArray[np.floating]]",
        ) -> bool:
            proj1 = float(directions1[0] @ directions2[0])
            proj2 = np.linalg.norm(np.cross(directions1[1], directions2[1]))
            primaries_aligned = 1.0 - proj1 < _alignment_tol
            secondaries_closest = bool(proj2 < _alignment_tol)
            return primaries_aligned and secondaries_closest

        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        orientations_aligned = []
        for orientation in orientations:
            check = any(
                _aligned(
                    orientation.directions, (d.direction, adsorption_site.norm)
                )
                for d in adsorption_site.alignments
            )
            orientations_aligned.append(check)

        assert all(orientations_aligned)

    @staticmethod
    @pytest.mark.parametrize("sym_order", [2, 4])
    @pytest.mark.parametrize("adsorbate", ["H2", "CO2", "H2O"], indirect=True)
    @pytest.mark.parametrize("check_symmetry", [True])
    def test_should_exclude_symmetric_orientations_if_check_symmetry_true(
        transformer: Transformer,
        adsorption_site: AdsorptionSite,
        adsorbate: Atoms,
    ):
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        symmetric_orientations: list[Any] = []

        for orientation1, orientation2 in combinations(orientations, r=2):
            aligned1 = align(adsorbate, orientation1.directions)
            aligned2 = align(adsorbate, orientation2.directions)

            if Comparator.check_similarity(aligned1, aligned2):
                symmetric_orientations.append((orientation1, orientation2))

        assert not any(symmetric_orientations)

    @staticmethod
    @pytest.mark.parametrize("sym_order", [2])
    @pytest.mark.parametrize("adsorbate", ["H2", "CO2", "H2O"], indirect=True)
    def test_should_include_symmetric_orientations_if_check_symmetry_false(
        transformer: Transformer,
        adsorption_site: AdsorptionSite,
        adsorbate: Atoms,
    ) -> None:
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        assert len(orientations) == 2

    @staticmethod
    @pytest.mark.parametrize("check_symmetry", [True])
    @pytest.mark.parametrize("adsorbate", ["H", "C", "O", "N"], indirect=True)
    def test_should_return_single_orientation_for_zero_dimensional_adsorbate_if_check_symmetry_true(
        transformer: Transformer,
        adsorption_site: AdsorptionSite,
        adsorbate: Atoms,
    ):
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        assert len(orientations) == 1

    @staticmethod
    @pytest.mark.parametrize("check_symmetry", [False])
    def test_should_return_one_orientation_for_every_transformation_with_single_site_and_alignment_and_check_symmetry_false(
        transformer: Transformer,
        adsorption_site: AdsorptionSite,
        adsorbate: Atoms,
    ):
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        assert len(orientations) == len(transformer.transformations)

    @staticmethod
    @pytest.mark.parametrize("check_symmetry", [False])
    @pytest.mark.parametrize("alignments", [2, 3, 4])
    @pytest.mark.parametrize("sym_order", [2, 3, 4])
    @pytest.mark.parametrize(
        "adsorbate",
        ["H2", "CO", "CO2", "OH", "NHO", "COOH", "CH3", "NH2OH"],
        indirect=True,
    )
    def test_should_return_same_number_of_orientations_as_product_of_alignments_and_transformations_for_non_zero_dimensional_adsorbate_if_check_symmetry_false(
        transformer: Transformer,
        adsorption_site: AdsorptionSite,
        adsorbate: Atoms,
    ):
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        assert len(orientations) == len(adsorption_site.alignments) * (
            len(transformer.transformations)
        )

    @staticmethod
    def test_should_return_two_orientations_for_d4h_symmetric_molecule_and_octahedral_transformer_when_check_symmetry_is_true(
        adsorption_site: AdsorptionSite,
    ) -> None:
        transformer = OctahedralFactory(check_symmetry=True)
        adsorbate = Atoms(
            "XeF4",
            positions=[
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [-1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, -1.0, 0.0],
            ],
        )
        orientations = transformer(
            adsorption_site, adsorbate, _get_com(adsorbate)
        )
        assert len(orientations) == 2
