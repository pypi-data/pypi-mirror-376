import logging

from ase import Atoms
from ase.cell import Cell
import pytest

from ccu.structure.defects import _convert_occupancies_to_occupants
from ccu.structure.defects import _validate_occupancies
from ccu.structure.defects import permute

logger = logging.getLogger(__name__)


class TestValidateOccupancies:
    @staticmethod
    def test_should_return_true_if_number_of_occupancies_less_than_number_of_sites() -> (
        None
    ):
        occupancies = [("Cu", 1)]
        sites = [0, 1]
        assert _validate_occupancies(sites=sites, occupancies=occupancies)

    @staticmethod
    def test_should_return_true_if_number_of_occupancies_equal_to_number_of_sites() -> (
        None
    ):
        occupancies = [("Cu", 1)]
        sites = [0]
        assert _validate_occupancies(sites=sites, occupancies=occupancies)

    @staticmethod
    def test_should_return_false_if_number_of_occupancies_greater_than_number_of_sites() -> (
        None
    ):
        occupancies = [("Cu", 1), ("Cu", 1)]
        sites = [0]
        assert not _validate_occupancies(sites=sites, occupancies=occupancies)


class TestConvertOccupanciesToOccupants:
    @staticmethod
    def test_should_work() -> None:
        occupancies = [("Cu", 1), ("Cu", 1)]
        occupants = _convert_occupancies_to_occupants(occupancies=occupancies)
        assert occupants == ["Cu", "Cu"]


class TestPermute:
    @staticmethod
    def test_should_return_same_structure_if_sites_empty() -> None:
        atoms = Atoms("C")
        assert permute(structure=atoms, sites=[], occupancies=[("C", 0)]) == [
            atoms
        ]

    @staticmethod
    def test_should_permute_all_sites_if_sites_not_set() -> None:
        cell = Cell([[5, 0, 0], [0, 5, 0], [0, 0, 5]])
        positions = [[0, 0, 0], [1, 0, 0], [0, 0, 1], [1, 1, 1]]
        symbols = sorted("COHB")
        atoms = Atoms(symbols, cell=cell, positions=positions, pbc=True)
        perms = permute(structure=atoms)
        assert len(perms) > 1

    # TODO
    @staticmethod
    def test_should_permute_all_atoms_in_sites_if_occupancies_not_set() -> (
        None
    ): ...

    @staticmethod
    def test_should_raise_value_error_if_more_occupancies_than_sites() -> None:
        atoms = Atoms("C")
        with pytest.raises(ValueError, match="Number of sites to replace"):
            permute(structure=atoms, sites=[], occupancies=[("C", 1)])

    @staticmethod
    def test_should_return_same_structure_if_occupancies_empty() -> None:
        atoms = Atoms("C")
        assert permute(structure=atoms, sites=[0], occupancies=[]) == [atoms]
