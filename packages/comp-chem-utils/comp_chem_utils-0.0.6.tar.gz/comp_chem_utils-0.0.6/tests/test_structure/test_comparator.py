from copy import deepcopy
from itertools import permutations
import time

from ase.atoms import Atoms
from ase.symbols import string2symbols
import numpy as np
from numpy.testing import assert_allclose
import pytest

from ccu.structure.comparator import Comparator
from ccu.structure.fingerprint import Fingerprint


@pytest.fixture(name="structure", params=["HH", "CH", "XeF4"])
def fixture_structure(request) -> Atoms:
    positions = [
        np.zeros(3),
        np.identity(3)[0],
        -np.identity(3)[0],
        np.identity(3)[1],
        -np.identity(3)[1],
        np.identity(3)[2],
        -np.identity(3)[2],
    ]
    formula = string2symbols(str(request.param))
    return Atoms(formula, positions=positions[: len(formula)])


@pytest.fixture(name="fingerprint")
def fixture_fingerprint(structure: Atoms) -> Fingerprint:
    return Fingerprint(structure, 0, range(len(structure)))


@pytest.fixture(name="fingerprints")
def fixture_fingerprints(structure) -> list[Fingerprint]:
    return Fingerprint.from_structure(structure)


class TestCheckSimilarity:
    @staticmethod
    def structure_from_chemical_symbols(chemical_symbols: str) -> Atoms:
        positions = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        atomic_positions = []
        for i, _ in enumerate(chemical_symbols):
            atomic_positions.append(positions[i])

        return Atoms(chemical_symbols, positions=atomic_positions)

    # test identical structures
    @staticmethod
    @pytest.mark.parametrize("chemical_symbols", ["HH", "CH", "CHO"])
    def test_should_return_true_for_identical_structure(chemical_symbols: str):
        atoms = TestCheckSimilarity.structure_from_chemical_symbols(
            chemical_symbols
        )
        assert Comparator.check_similarity(atoms, atoms)

    @staticmethod
    @pytest.mark.parametrize("chemical_symbols", ["HH", "CH", "CHO"])
    def test_should_return_true_if_structure_perturbed_less_than_tolerance(
        chemical_symbols: str,
    ) -> None:
        atoms1 = TestCheckSimilarity.structure_from_chemical_symbols(
            chemical_symbols
        )
        atoms2 = atoms1.copy()
        for i, _ in enumerate(atoms2):
            atoms2.positions[i] += (i + 1) * 1e-3
        assert Comparator.check_similarity(atoms1, atoms2)

    @staticmethod
    @pytest.mark.parametrize("chemical_symbols", ["HH", "CH", "CHO"])
    def test_should_return_true_if_structure_translated(
        chemical_symbols: str,
    ) -> None:
        atoms1 = TestCheckSimilarity.structure_from_chemical_symbols(
            chemical_symbols
        )
        atoms2 = atoms1.copy()
        atoms2.positions += 1
        assert Comparator.check_similarity(atoms1, atoms2)

    # test identical, rotated structures
    @staticmethod
    @pytest.mark.parametrize("chemical_symbols", ["HH", "CH", "CHO"])
    def test_should_return_false_for_identical_but_rotated_structure(
        chemical_symbols: str,
    ) -> None:
        atoms1 = TestCheckSimilarity.structure_from_chemical_symbols(
            chemical_symbols
        )
        atoms2 = atoms1.copy()
        atoms2.rotate([1, 0, 0], [0, 1, 0])
        assert not Comparator.check_similarity(atoms1, atoms2)

    @staticmethod
    @pytest.mark.parametrize("chemical_symbols", ["HH", "CH", "CHO"])
    def test_should_return_false_if_structure_perturbed_more_than_tolerance(
        chemical_symbols: str,
    ) -> None:
        atoms1 = TestCheckSimilarity.structure_from_chemical_symbols(
            chemical_symbols
        )
        atoms2 = atoms1.copy()
        for i, _ in enumerate(atoms2):
            atoms2.positions[i] += (i + 1) * 1e-1
        assert not Comparator.check_similarity(atoms1, atoms2)


class TestCosortHistograms:
    @staticmethod
    def test_should_reorder_identical_histograms_to_match(
        fingerprint: Fingerprint,
    ) -> None:
        fingerprint1 = deepcopy(fingerprint)
        fingerprint2 = deepcopy(fingerprint)
        res = []

        fingerprint2.update(
            Comparator.cosort_histograms(fingerprint1, fingerprint2)
        )

        for element in fingerprint2:
            displacements1 = fingerprint1[element]
            for i, displacement2 in enumerate(fingerprint2[element]):
                displacement1 = displacements1[i]
                res.append((displacement1 == displacement2).all())

        assert False not in res

    @staticmethod
    def test_should_reorder_identical_reversed_histograms_to_match(
        structure: Atoms,
        fingerprint: Fingerprint,
    ) -> None:
        atom = str(structure[0].symbol)
        fingerprint1 = deepcopy(fingerprint)
        fingerprint2 = deepcopy(fingerprint)
        fingerprint2[atom] = np.flip(fingerprint2[atom], axis=0)
        res = []

        fingerprint2.update(
            Comparator.cosort_histograms(fingerprint1, fingerprint2)
        )

        for element in fingerprint2:
            displacements1 = fingerprint1[element]
            for i, displacement2 in enumerate(fingerprint2[element]):
                displacement1 = displacements1[i]
                res.append((displacement1 == displacement2).all())

        assert False not in res

    @staticmethod
    def test_should_reorder_histograms_when_first_fingerprint_has_longer_entry(
        structure: Atoms,
        fingerprint: Fingerprint,
    ) -> None:
        atom = str(structure[0].symbol)
        fingerprint1 = deepcopy(fingerprint)
        fingerprint1[atom] = np.vstack([fingerprint1[atom], [2, 0, 0]])
        fingerprint2 = deepcopy(fingerprint)
        fingerprint2[atom] = np.flip(fingerprint2[atom], axis=0)
        res = []

        fingerprint2.update(
            Comparator.cosort_histograms(fingerprint1, fingerprint2)
        )

        for element in fingerprint2:
            displacements1 = fingerprint1[element]
            for i, displacement2 in enumerate(fingerprint2[element]):
                displacement1 = displacements1[i]
                res.append((displacement1 == displacement2).all())

        assert False not in res

    @staticmethod
    def test_should_reorder_histograms_when_second_fingerprint_has_longer_entry(
        structure: Atoms,
        fingerprint: Fingerprint,
    ) -> None:
        atom = str(structure[0].symbol)
        fingerprint1 = deepcopy(fingerprint)
        fingerprint2 = deepcopy(fingerprint)
        fingerprint2[atom] = np.flip(fingerprint2[atom], axis=0)
        fingerprint2[atom] = np.vstack([fingerprint2[atom], [2, 0, 0]])
        res = []

        fingerprint2.update(
            Comparator.cosort_histograms(fingerprint1, fingerprint2)
        )

        for element in fingerprint1:
            displacements2 = fingerprint2[element]
            for i, displacement1 in enumerate(fingerprint1[element]):
                displacement2 = displacements2[i]
                res.append((displacement1 == displacement2).all())

        assert False not in res


# The tolerance for the minimal displacement for equivalent structure
_MIN_DISP_TOL = 1e-14


class TestCosortFingerprints:
    @staticmethod
    @pytest.fixture(name="angle")
    def fixture_angle(request: pytest.FixtureRequest) -> int:
        return int(request.param)

    @staticmethod
    def test_should_unchange_identical_histograms(
        structure: Atoms, fingerprints: tuple[Fingerprint, ...]
    ) -> None:
        atom = str(structure[0].symbol)
        fingerprints1 = deepcopy(fingerprints)
        fingerprints2 = deepcopy(fingerprints)
        res = []

        fingerprints2 = Comparator.cosort_fingerprints(
            fingerprints1, fingerprints2
        )

        for i, fingerprint2 in enumerate(fingerprints2):
            fingerprint1 = fingerprints1[i]
            for j, displacement2 in enumerate(fingerprint2[atom]):
                displacement1 = fingerprint1[atom][j]
                res.append((displacement1 == displacement2).all())

        assert False not in res

    @staticmethod
    def test_should_reorder_identical_reversed_fingerprints_to_match(
        structure: Atoms,
        fingerprints: tuple[Fingerprint, ...],
    ) -> None:
        atom = str(structure[0].symbol)
        fingerprints1 = deepcopy(fingerprints)
        fingerprints2 = deepcopy(fingerprints)
        fingerprints2[0][atom] = np.flip(fingerprints2[0][atom], axis=0)
        fingerprints2[1][atom] = np.flip(fingerprints2[1][atom], axis=0)
        res = []

        fingerprints2 = Comparator.cosort_fingerprints(
            fingerprints1, fingerprints2
        )

        for i, fingerprint2 in enumerate(fingerprints2):
            fingerprint1 = fingerprints1[i]
            for j, displacement2 in enumerate(fingerprint2[atom]):
                displacement1 = fingerprint1[atom][j]
                res.append((displacement1 == displacement2).all())

        assert False not in res

    @classmethod
    @pytest.mark.parametrize(
        ("angle", "structure"),
        [(180, "HH"), (90, "XeF4")],
        indirect=True,
    )
    def test_should_find_zero_displacement_ordering_for_rotation_in_symmetry_group(
        cls, structure: Atoms, angle: int
    ) -> None:
        rotated = structure.copy()
        rotated.rotate(angle, "z")
        fingerprints1 = Fingerprint.from_structure(structure=structure)
        fingerprints2 = tuple(Fingerprint.from_structure(structure=rotated))
        start = time.time()
        fingerprints2 = Comparator.cosort_fingerprints(
            fingerprints1, fingerprints2
        )
        end = time.time()
        disp = Comparator.calculate_cumulative_displacement(
            fingerprints1[0], fingerprints2[0]
        )
        assert disp < _MIN_DISP_TOL

    @classmethod
    @pytest.mark.parametrize(
        "structure",
        ["HH", "XeF4"],
        indirect=True,
    )
    def test_should_find_zero_displacement_ordering_for_index_permutation(
        cls,
        structure: Atoms,
    ) -> None:
        fingerprints1 = Fingerprint.from_structure(structure=structure)
        perms = [p for i, p in enumerate(permutations(structure)) if i < 4]
        displacements = np.zeros(len(perms))

        for i, perm in enumerate(perms):
            permuted = Atoms(perm)
            fingerprints2 = tuple(
                Fingerprint.from_structure(structure=permuted)
            )
            fingerprints2 = Comparator.cosort_fingerprints(
                fingerprints1, fingerprints2
            )
            disp = Comparator.calculate_cumulative_displacement(
                fingerprints1[0], fingerprints2[0]
            )
            displacements[i] = disp
        assert_allclose(
            displacements, np.zeros(len(displacements)), atol=_MIN_DISP_TOL
        )

    @classmethod
    @pytest.mark.parametrize(
        "structure",
        ["HH", "XeF4"],
        indirect=True,
    )
    def test_should_find_zero_displacement_ordering_for_reflection_in_symmetry_group(
        cls,
        structure: Atoms,
    ) -> None:
        fingerprints1 = Fingerprint.from_structure(structure=structure)
        displacements = np.zeros(3)

        for i in range(3):
            reflected = structure.copy()
            vec = np.ones(3)
            vec[i] = -1
            reflected.positions *= -vec
            fingerprints2 = tuple(
                Fingerprint.from_structure(structure=reflected)
            )
            fingerprints2 = Comparator.cosort_fingerprints(
                fingerprints1, fingerprints2
            )
            disp = Comparator.calculate_cumulative_displacement(
                fingerprints1[0], fingerprints2[0]
            )
            displacements[i] = disp

        assert_allclose(
            displacements, np.zeros(len(displacements)), atol=_MIN_DISP_TOL
        )


class TestCalculateCumulativeDisplacement:
    @staticmethod
    def test_should_return_zero_for_identical_fingerprints(
        fingerprint: Fingerprint,
    ) -> None:
        assert (
            Comparator.calculate_cumulative_displacement(
                fingerprint, fingerprint
            )
            == 0
        )

    @staticmethod
    def test_should_return_correct_displacement_for_nonidentical_fingerprints(
        fingerprint: Fingerprint,
    ) -> None:
        fingerprint_copy = deepcopy(fingerprint)
        count = 0
        for element in fingerprint_copy:
            displacements = fingerprint_copy[element]
            for i, _ in enumerate(displacements):
                # Displace each atom by exactly 1.0 Angstrom to result in
                # a cumulative displacement equal to the number of atoms
                # represented by the fingerprint
                displacements[i] += [1, 0, 0]
                count += 1

        assert (
            Comparator.calculate_cumulative_displacement(
                fingerprint, fingerprint_copy
            )
            == count
        )
