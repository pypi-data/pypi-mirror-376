# pylint:disable=protected-access

from copy import deepcopy

import ase
import numpy as np
import pytest

from ccu.structure.fingerprint import Fingerprint


@pytest.fixture(name="structure")
def fixture_structure() -> ase.Atoms:
    return ase.Atoms("CH", positions=[[0, 0, 0], [1, 0, 0]])


@pytest.fixture(name="fingerprint")
def fixture_fingerprint(structure) -> Fingerprint:
    return Fingerprint(structure, 0, [0, 1])


@pytest.fixture(name="fingerprints")
def fixture_fingerprints(structure) -> list[Fingerprint]:
    return Fingerprint.from_structure(structure)


class TestConstructor:
    @staticmethod
    def test_should_record_correct_displacement_for_each_index_in_fingerprint1(
        fingerprint,
    ):
        assert (fingerprint._histogram["C"][0] == np.zeros(3)).all()

    @staticmethod
    def test_should_record_correct_displacement_for_each_index_in_fingerprint2(
        fingerprint,
    ):
        assert (fingerprint._histogram["H"][0] == [1, 0, 0]).all()

    # pylint:disable=line-too-long
    @staticmethod
    def test_should_record_correct_chemical_symbol_for_each_index_in_fingerprint1(
        fingerprint,
    ):
        assert "C" in fingerprint._histogram

    # pylint:disable=line-too-long
    @staticmethod
    def test_should_record_correct_chemical_symbol_for_each_index_in_fingerprint2(
        fingerprint,
    ):
        assert "H" in fingerprint._histogram

    @staticmethod
    def test_should_record_correct_number_of_chemical_symbols_in_histogram(
        fingerprint,
    ):
        assert len(fingerprint._histogram) == 2


class TestMutableMappingMethods:
    @staticmethod
    def test_should_get_item_at_index(fingerprint):
        assert (fingerprint["C"][0] == np.zeros(3)).all()

    @staticmethod
    def test_should_set_item_at_key(fingerprint):
        fingerprint_copy = deepcopy(fingerprint)
        new_value = np.array([[1, 1, 1], [2, 2, 2]])
        fingerprint_copy["C"] = new_value
        res = []
        for i, row in enumerate(new_value):
            res.append((row == fingerprint_copy["C"][i]).all())

        assert False not in res

    @staticmethod
    def test_should_delete_item_at_index(fingerprint):
        fingerprint_copy = deepcopy(fingerprint)
        del fingerprint_copy["C"]
        assert "C" not in fingerprint_copy

    @staticmethod
    def test_should_return_correct_length(fingerprint):
        assert len(fingerprint) == 2


class TestFromStructure:
    @staticmethod
    def test_should_number_of_fingerprints_equal_to_number_of_atoms(
        structure, fingerprints
    ):
        assert len(fingerprints) == len(structure)

    @staticmethod
    def test_should_create_fingerprint_with_correct_displacements1(
        fingerprints,
    ):
        assert (fingerprints[0]["C"][0] == np.zeros(3)).all()

    @staticmethod
    def test_should_create_fingerprint_with_correct_displacements2(
        fingerprints,
    ):
        assert (fingerprints[0]["H"][0] == [1, 0, 0]).all()

    @staticmethod
    def test_should_create_fingerprint_with_correct_displacements3(
        fingerprints,
    ):
        assert (fingerprints[1]["C"][0] == [-1, 0, 0]).all()

    @staticmethod
    def test_should_create_fingerprint_with_correct_displacements4(
        fingerprints,
    ):
        assert (fingerprints[1]["H"][0] == np.zeros(3)).all()

    @staticmethod
    def test_should_create_fingerprint_with_correct_chemical_symbols1(
        fingerprints,
    ):
        assert "C" in fingerprints[0]

    @staticmethod
    def test_should_create_fingerprint_with_correct_chemical_symbols2(
        fingerprints,
    ):
        assert "H" in fingerprints[0]

    @staticmethod
    def test_should_create_fingerprint_with_correct_chemical_symbols3(
        fingerprints,
    ):
        assert "C" in fingerprints[1]

    @staticmethod
    def test_should_create_fingerprint_with_correct_chemical_symbols4(
        fingerprints,
    ):
        assert "H" in fingerprints[1]
