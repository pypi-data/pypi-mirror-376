from math import isclose

from ase.atoms import Atoms
import numpy as np
import pytest

from ccu.structure.symmetry import Inversion
from ccu.structure.symmetry import Reflection
from ccu.structure.symmetry import Rotation


@pytest.fixture(name="molecule")
def fixture_molecule() -> Atoms:
    return Atoms("CO", positions=[[0, 0, 0], [1, 0, 0]])


class TestRotation:
    @staticmethod
    def test_should_not_change_molecule_when_rotation_is_symmetry_operation(
        molecule: Atoms,
    ):
        rotation = Rotation(180, [1, 0, 0])
        rotated = rotation(molecule)

        res = []
        for i, position in enumerate(molecule.positions):
            res.append((position == rotated.positions[i]).all())

        assert False not in res

    @staticmethod
    def test_should_correctly_rotate_molecule(molecule: Atoms):
        rotation = Rotation(180, [0, 0, 1])
        rotated = rotation(molecule)

        res = []
        for i, position in enumerate(molecule.positions):
            check = True
            for j, coordinate in enumerate(position):
                if not isclose(
                    coordinate, -rotated.positions[i][j], abs_tol=1e-10
                ):
                    check = False
                    break
            res.append(check)

        assert False not in res

    @staticmethod
    def test_should_return_correct_matrix1():
        rotation = Rotation(90, [0, 0, 1])
        matrix = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        res = []
        rot_matrix = rotation.as_matrix()
        for i, vec1 in enumerate(matrix):
            vec2 = rot_matrix[i]
            check = True
            for j, coordinate1 in enumerate(vec1):
                coordinate2 = vec2[j]
                if not isclose(coordinate1, coordinate2, abs_tol=1e-5):
                    check = False
                    break
            res.append(check)

        assert False not in res

    @staticmethod
    def test_should_return_correct_matrix2():
        rotation = Rotation(90, [0, 1, 0])
        matrix = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
        res = []
        rot_matrix = rotation.as_matrix()
        for i, vec1 in enumerate(matrix):
            vec2 = rot_matrix[i]
            check = True
            for j, coordinate1 in enumerate(vec1):
                coordinate2 = vec2[j]
                if not isclose(coordinate1, coordinate2, abs_tol=1e-5):
                    check = False
                    break
            res.append(check)

        assert False not in res

    @staticmethod
    def test_should_return_correct_matrix3():
        rotation = Rotation(90, [1, 0, 0])
        matrix = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
        res = []
        rot_matrix = rotation.as_matrix()
        for i, vec1 in enumerate(matrix):
            vec2 = rot_matrix[i]
            check = True
            for j, coordinate1 in enumerate(vec1):
                coordinate2 = vec2[j]
                if not isclose(coordinate1, coordinate2, abs_tol=1e-5):
                    check = False
                    break
            res.append(check)

        assert False not in res


class TestInversion:
    @staticmethod
    def test_should_invert_positions_through_origin(molecule: Atoms) -> None:
        invert = Inversion()
        inverted = invert(molecule)
        assert (inverted[0].position == np.zeros(3)).all()
        assert (inverted[1].position == -molecule[1].position).all()

    @staticmethod
    def test_should_invert_positions_through_non_origin_point(
        molecule: Atoms,
    ) -> None:
        invert = Inversion(molecule[1].position)
        inverted = invert(molecule)
        assert (inverted[0].position == [2.0, 0.0, 0.0]).all()
        assert (inverted[1].position == molecule[1].position).all()


class TestReflection:
    @staticmethod
    def test_should_reflect_positions_through_yz_plane(
        molecule: Atoms,
    ) -> None:
        reflect = Reflection(norm=[1.0, 0.0, 0.0])
        reflected = reflect(molecule)
        assert (reflected[0].position == np.zeros(3)).all()
        assert (reflected[1].position == -molecule[1].position).all()

    @staticmethod
    def test_should_reflect_positions_through_plane_parallel_to_yz_plane(
        molecule: Atoms,
    ) -> None:
        reflect = Reflection(point=[1.0, 0.0, 0.0], norm=[1.0, 0.0, 0.0])
        reflected = reflect(molecule)
        assert (reflected[0].position == [2.0, 0.0, 0.0]).all()
        assert (reflected[1].position == molecule[1].position).all()
