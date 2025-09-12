from random import Random
from typing import TYPE_CHECKING

import ase
from ase.atoms import Atoms
from ase.build import molecule
import numpy as np
import pytest

from ccu.adsorption.adsorbates import get_adsorbate
from ccu.structure.axisfinder import find_primary_axis
from ccu.structure.axisfinder import find_tertiary_axis
from ccu.structure.geometry import align
from ccu.structure.geometry import calculate_norm
from ccu.structure.geometry import calculate_separation

if TYPE_CHECKING:
    from numpy.typing import NDArray


class TestCalculateSeparation:
    @staticmethod
    def test_should_return_zero_for_identical_structures():
        co = molecule("CO")
        assert calculate_separation(co, co) == 0

    @staticmethod
    def test_should_return_distance_between_single_atom_structures():
        c = ase.Atoms("C", positions=[[0, 0, 0]])
        o = ase.Atoms("O", positions=[[1, 0, 0]])
        assert calculate_separation(c, o) == 1

    @staticmethod
    def test_should_return_distance_between_polyatomic_structures():
        co2 = ase.Atoms("CO2", positions=[[0, 0, 0], [0, 1, 0], [0, -1, 0]])
        co2_shifted = ase.Atoms(
            "CO2", positions=[[0, 0, 0], [0, 1, 0], [0, -1, 0]]
        )
        co2_shifted.positions += [10, 0, 0]
        assert calculate_separation(co2, co2_shifted) == 10


class TestCalculateNorm:
    @staticmethod
    @pytest.fixture(
        name="norm",
        params=[
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [-1.0, 0.0, 1.0],
            [0.0, -1.0, 1.0],
        ],
    )
    def fixture_norm(request: pytest.FixtureRequest) -> "NDArray[np.floating]":
        return np.array(request.param)

    @staticmethod
    @pytest.fixture(name="num_points", params=range(3, 10))
    def fixture_num_points(request: pytest.FixtureRequest) -> int:
        return int(request.param)

    @staticmethod
    @pytest.fixture(name="displace_sites")
    def fixture_displace_sites() -> bool:
        return False

    @staticmethod
    @pytest.fixture(name="points")
    def fixture_points(
        norm: "NDArray[np.floating]", num_points: int, displace_sites: bool
    ) -> "list[NDArray[np.floating]]":
        basis = np.identity(3)
        # ensure that the coordinates corresponding to first and second
        # elements can be freely chosen in the plane
        indices = [1, 2, 0] if norm @ basis[0] in (1.0, -1.0) else [0, 1, 2]
        if norm @ basis[indices[1]] in (1.0, -1.0):
            placeholder = indices[1]
            indices[1] = indices[2]
            indices[2] = placeholder

        # calculate the third coordinate for randomly chosen first and second
        # coordinates
        def _get_k(i, j, ind) -> float:
            if norm[ind[2]] == 0.0:
                return 1.0
            return -(i * norm[ind[0]] + j * norm[ind[1]]) / norm[ind[2]]

        points: list[NDArray[np.floating]] = []
        # Random number not security-related
        ran = Random(123)  # noqa: S311

        for _ in range(num_points):
            i = ran.random() * 10.0
            j = ran.random() * 10.0
            k = _get_k(i, j, indices)
            point = np.zeros(3)
            for n, val in zip(indices, [i, j, k], strict=True):
                point[n] = val + ran.random() / 1e2 if displace_sites else val
            points.append(point)
        return points

    @staticmethod
    @pytest.fixture(name="reverse", params=[True, False])
    def fixture_reverse(request: pytest.FixtureRequest) -> bool:
        return bool(request.param)

    @staticmethod
    def test_should_calculate_norm_as_parallel_to_plane_norm_vector_for_planar_sites(
        norm: "NDArray[np.floating]",
        points: "list[NDArray[np.floating]]",
        reverse: bool,
    ) -> None:
        calculated_norm = calculate_norm(points, reverse=reverse)
        assert np.linalg.norm(np.cross(norm, calculated_norm)) == 0.0

    @staticmethod
    @pytest.mark.parametrize("displace_sites", [True])
    def test_should_calculate_norm_as_close_to_plane_norm_vector_for_slightly_displaced_sites(
        norm: "NDArray[np.floating]",
        points: "list[NDArray[np.floating]]",
        reverse: bool,
    ) -> None:
        calculated_norm = calculate_norm(points, reverse=reverse)
        assert np.linalg.norm(np.cross(norm, calculated_norm)) <= 1e-2

    @staticmethod
    @pytest.mark.parametrize("reverse", [False])
    def test_should_return_upper_hemisphere_vector_when_reverse_is_false(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[-1] >= 0

    @staticmethod
    @pytest.mark.parametrize("reverse", [True])
    def test_should_return_lower_hemisphere_vector_when_reverse_is_true(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[-1] <= 0

    @staticmethod
    @pytest.mark.parametrize(
        "norm",
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, -1.0, 0.0],
        ],
    )
    @pytest.mark.parametrize("reverse", [False])
    def test_should_return_positive_y_norm_when_norm_in_xy_plane_and_reverse_is_false(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[1] >= 0

    @staticmethod
    @pytest.mark.parametrize(
        "norm",
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
            [1.0, -1.0, 0.0],
        ],
    )
    @pytest.mark.parametrize("reverse", [True])
    def test_should_return_negative_y_norm_when_norm_in_xy_plane_and_reverse_is_true(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[1] <= 0

    @staticmethod
    @pytest.mark.parametrize("norm", [[1.0, 0.0, 0.0]])
    @pytest.mark.parametrize("reverse", [False])
    def test_should_return_positive_x_norm_when_plane_in_yz_plane_and_reverse_is_false(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[0] >= 0

    @staticmethod
    @pytest.mark.parametrize("norm", [[1.0, 0.0, 0.0]])
    @pytest.mark.parametrize("reverse", [True])
    def test_should_return_negative_x_norm_when_plane_in_yz_plane_and_reverse_is_true(
        points: "list[NDArray[np.floating]]", reverse: bool
    ) -> None:
        norm = calculate_norm(points, reverse=reverse)
        assert norm[0] <= 0


# Tolerance for alignment tests
_alignment_tol = 1e-6


@pytest.fixture(name="adsorbate", params=["H"])
def fixture_adsorbate(request) -> Atoms:
    return get_adsorbate(request.param)


@pytest.fixture(name="directions")
def fixture_directions() -> (
    "tuple[NDArray[np.floating], NDArray[np.floating]]"
):
    basis = np.identity(3)
    return basis[0], basis[1]


class TestAlign:
    @staticmethod
    @pytest.fixture(
        name="adsorbate",
        params=["H", "OH", "CO2", "NHO", "COOH", "CH3", "NH2OH"],
    )
    def fixture_adsorbate(request: pytest.FixtureRequest) -> Atoms:
        adsorbate = get_adsorbate(str(request.param))
        return adsorbate

    @staticmethod
    @pytest.mark.parametrize("adsorbate", ["H", "C", "O", "N"], indirect=True)
    def test_should_not_change_zero_dimensional_adsorbate(
        adsorbate: Atoms,
        directions: "tuple[NDArray[np.floating], NDArray[np.floating]]",
    ):
        aligned = align(adsorbate, directions)
        assert (
            adsorbate.get_positions()[0] == aligned.get_positions()[0]
        ).all()

    @staticmethod
    @pytest.mark.parametrize(
        "adsorbate",
        ["H2", "CO", "CO2", "OH", "NHO", "COOH", "CH3", "NH2OH"],
        indirect=True,
    )
    def test_should_orient_non_zero_dimensional_adsorbate_along_orientation_axis(
        adsorbate: Atoms,
        directions: "tuple[NDArray[np.floating], NDArray[np.floating]]",
    ):
        aligned = align(adsorbate, directions)
        primary = find_primary_axis(aligned)
        proj = directions[0] @ primary
        # Primary axis and first direction must be parallel (within tol)
        assert (1.0 - proj) < _alignment_tol

    @staticmethod
    @pytest.mark.parametrize(
        "adsorbate", ["NHO", "COOH", "CH3", "NH2OH"], indirect=True
    )
    def test_should_orient_multidimensional_adsorbate_along_second_orientation_axis(
        adsorbate: Atoms,
        directions: "tuple[NDArray[np.floating], NDArray[np.floating]]",
    ):
        aligned = align(adsorbate, directions)
        tertiary = find_tertiary_axis(aligned)
        proj = np.cross(*directions) @ tertiary
        # Normal vector of planes defined by "directions" and
        # primary and secondary axes of adsorbate must be parallel (within tol)
        assert (1.0 - proj) < _alignment_tol

    @staticmethod
    def test_should_not_move_atom_at_alignment_center(
        adsorbate: Atoms,
        directions: "tuple[NDArray[np.floating], NDArray[np.floating]]",
    ) -> None:
        center = adsorbate[0].position
        aligned = align(adsorbate, directions, center=center)
        assert (aligned[0].position == center).all()
