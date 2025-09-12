from itertools import product

import ase
from ase.build import molecule
import numpy as np
from numpy.linalg import norm
import pytest

from ccu.adsorption.adsorbates import get_adsorbate
from ccu.structure.axisfinder import find_farthest_atoms
from ccu.structure.axisfinder import find_primary_axis
from ccu.structure.axisfinder import find_secondary_axis
from ccu.structure.axisfinder import get_axes


# pylint:disable=line-too-long
class TestFindFarthestAtoms:
    @staticmethod
    @pytest.mark.parametrize("name", ["CO", "H2", "HF", "NO"])
    def test_should_define_farthest_atoms_stably(name: str):
        adsorbate = molecule(name)
        atom1, atom2 = find_farthest_atoms(adsorbate)
        assert (atom1.position == adsorbate.positions[0]).all()
        assert (atom2.position == adsorbate.positions[1]).all()

    @staticmethod
    @pytest.mark.parametrize(
        ("name", "index"), product(("NO3", "NH3", "CH4"), range(3))
    )
    def test_should_return_same_atoms_after_transformation(
        name: str, index: int
    ):
        adsorbate = get_adsorbate(name)
        atom1, atom2 = find_farthest_atoms(adsorbate)
        vector = np.zeros(3)
        vector[index] = 1
        adsorbate.rotate(vector, [1, 1, 1])
        atom3, atom4 = find_farthest_atoms(adsorbate)
        assert atom1.index == atom3.index
        assert atom2.index == atom4.index


class TestGetAxis:
    @staticmethod
    def test_should_return_cartesian_axes():
        adsorbate = molecule(
            "HCN",
            positions=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [1.0, 0.5, 0.0]],
        )
        primary, secondary, tertiary = get_axes(adsorbate)
        assert (primary == np.array([-1.0, 0.0, 0])).all()
        assert (secondary == np.array([0.0, 1.0, 0])).all()
        assert (tertiary == np.array([0.0, 0.0, -1.0])).all()


class TestFindPrimaryAxis:
    @staticmethod
    def test_should_return_zero_vector_for_monoatomic_molecule():
        atoms = ase.Atoms("H")
        axis = find_primary_axis(atoms)
        assert (axis == np.zeros(3)).all()

    @staticmethod
    @pytest.mark.parametrize("name", ["CO", "H2", "CH4"])
    def test_should_return_unit_vector(name: str):
        atoms = molecule(name)
        axis = find_primary_axis(atoms)
        assert norm(axis) == 1

    @staticmethod
    def test_should_define_primary_axis_based_on_farthest_atoms():
        atoms = ase.Atoms("CHO", positions=[[0, 0, 0], [2, 0, 0], [-1, 0, 0]])
        axis = find_primary_axis(atoms)
        assert (axis == [1, 0, 0]).all()


class TestFindSecondaryAxis:
    @staticmethod
    def test_should_return_zero_vector_for_monoatomic_molecule():
        atoms = ase.Atoms("H")
        axis = find_secondary_axis(atoms)
        assert (axis == np.zeros(3)).all()

    @staticmethod
    @pytest.mark.parametrize("name", ["CO", "H2", "CO2"])
    def test_should_return_zero_vector_for_linear_molecule(name: str):
        atoms = molecule(name)
        axis = find_secondary_axis(atoms)
        assert (axis == np.zeros(3)).all()

    @staticmethod
    def test_should_define_secondary_axis_based_on_atom_farthest_from_primary_axis():
        atoms = ase.Atoms(
            "CHO", positions=[[0, 0, 0], [2, 0, 0], [1, -0.5, 0]]
        )
        axis = find_secondary_axis(atoms)
        assert (axis == [0, -1, 0]).all()
