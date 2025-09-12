import ase
from ase.build import molecule
import pytest

from ccu.structure.symmetry import Rotation
from ccu.structure.symmetry import check_symmetry


@pytest.fixture(name="structure_180", params=["H", "H2", "CO2", "COOH"])
def fixture_structure_180(request) -> ase.Atoms:
    positions = [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1]]
    symbols = request.param
    return ase.Atoms(symbols, positions=positions[: len(symbols)])


@pytest.fixture(name="asymmetric_structure", params=["BC", "BCN", "BCNO"])
def fixture_asymmetric_structure(request) -> ase.Atoms:
    positions = [[0, 0, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1]]
    symbols = request.param
    return ase.Atoms(symbols, positions=positions[: len(symbols)])


@pytest.fixture(name="rotation")
def fixture_rotation(request) -> Rotation:
    marker = request.node.get_closest_marker("rotation_angle")
    return Rotation(marker.args[0], [0, 0, 1])


class TestCheckSymmetry:
    # test for 30, 60, 90, 120, 180 symmetry
    @staticmethod
    @pytest.mark.rotation_angle(180)
    def test_should_identify_180_degree_rotation_symmetry(
        structure_180: ase.Atoms, rotation: Rotation
    ):
        assert check_symmetry(rotation, structure_180)

    @staticmethod
    @pytest.mark.rotation_angle(120)
    @pytest.mark.parametrize("structure", ["H", "NH3", "BF3"])
    def test_should_identify_120_degree_rotation_symmetry(
        structure: str, rotation: Rotation
    ):
        atoms = molecule(structure)
        assert check_symmetry(rotation, atoms)

    @staticmethod
    @pytest.mark.rotation_angle(90)
    def test_should_identify_90_degree_rotation_symmetry(rotation: Rotation):
        atoms = ase.Atoms(
            "XeF4",
            positions=[
                [0, 0, 0],
                [1, 0, 0],
                [0, 1, 0],
                [-1, 0, 0],
                [0, -1, 0],
            ],
        )
        assert check_symmetry(rotation, atoms)

    @staticmethod
    @pytest.mark.rotation_angle(180)
    def test_should_return_false_for_asymmetric_molecule1(
        asymmetric_structure: ase.Atoms, rotation: Rotation
    ):
        assert not check_symmetry(rotation, asymmetric_structure)

    @staticmethod
    @pytest.mark.rotation_angle(120)
    def test_should_return_false_for_asymmetric_molecule2(
        asymmetric_structure: ase.Atoms, rotation: Rotation
    ):
        assert not check_symmetry(rotation, asymmetric_structure)

    @staticmethod
    @pytest.mark.rotation_angle(90)
    def test_should_return_false_for_asymmetric_molecule3(
        asymmetric_structure: ase.Atoms, rotation: Rotation
    ):
        assert not check_symmetry(rotation, asymmetric_structure)
