from copy import deepcopy
from math import isclose
from pathlib import Path

import ase
from ase.calculators.vasp.setups import setups_defaults
from ase.calculators.vasp.vasp import Vasp
from ase.io import read
import numpy as np
import pytest

from ccu.workflows.hubbard_u import _configure_for_hubbard
from ccu.workflows.hubbard_u import _verify_hubbard_parameters
from ccu.workflows.hubbard_u import get_hubbard_u


@pytest.fixture(name="nio")
def fixture_nio(datadir) -> ase.Atoms:
    atoms = read(Path(datadir, "NiO.traj"))
    atoms = atoms[-1] if isinstance(atoms, list) else atoms
    return atoms


@pytest.fixture(name="calc")
def fixture_calc(nio: ase.Atoms) -> Vasp:
    return Vasp(
        prec="Accurate",
        ediff=1e-6,
        ismear=0,
        sigma=0.2,
        ispin=2,
        lorbit=11,
        lmaxmix=4,
        atoms=nio,
    )


class TestGetHubbardU:
    @staticmethod
    @pytest.mark.skipif("not os.getenv('VASP_SCRIPT')")
    def test_should_validate_vasp_example(calc: Vasp, nio: ase.Atoms):
        index = 0
        assert isclose(get_hubbard_u(calc, nio, index), 5.2, abs_tol=2e-1)
        assert "Ni" in nio.get_chemical_symbols()


class TestConfigureForHubbard:
    @staticmethod
    def test_should_set_atoms_in_calc(nio: ase.Atoms, calc: Vasp):
        new_calc = deepcopy(calc)
        _configure_for_hubbard(new_calc, nio)
        assert nio == new_calc.atoms

    @staticmethod
    @pytest.mark.parametrize("index", range(3))
    def test_should_add_custom_setup(calc: Vasp, nio: ase.Atoms, index):
        new_calc = deepcopy(calc)
        _configure_for_hubbard(new_calc, nio, index)
        assert (
            new_calc.input_params["setups"] is None
            or index in new_calc.input_params["setups"]
        )

    @staticmethod
    @pytest.mark.parametrize("index", range(3))
    def test_should_add_pp_of_custom_setup(calc: Vasp, nio: ase.Atoms, index):
        new_calc = deepcopy(calc)
        _configure_for_hubbard(new_calc, nio, index)
        symbol = nio.get_chemical_symbols()[index]
        suffix = setups_defaults["recommended"].get(symbol, "")
        pseudop = symbol + suffix
        assert (
            new_calc.input_params["setups"] is None
            or new_calc.input_params["setups"][index] == pseudop
        )

    @staticmethod
    @pytest.mark.parametrize("index", range(3))
    def test_should_set_ldautype(calc: Vasp, nio: ase.Atoms, index):
        new_calc = deepcopy(calc)
        _configure_for_hubbard(new_calc, nio, index)
        assert new_calc.int_params["ldautype"] == 3


class TestVerifyHubbardParameters:
    @staticmethod
    @pytest.mark.parametrize("icharg", range(9, 12))
    def test_should_set_icharg_less_than_ten_or_none(calc: Vasp, icharg: int):
        new_calc = deepcopy(calc)
        new_calc.set(icharg=icharg)
        _verify_hubbard_parameters(new_calc)
        assert (
            calc.int_params["icharg"] is None or calc.int_params["icharg"] < 10
        )

    @staticmethod
    @pytest.mark.parametrize("ldauu", range(9, 12))
    def test_should_set_ldauu_to_zero(nio: ase.Atoms, calc: Vasp, ldauu: int):
        new_calc = deepcopy(calc)
        new_calc.set(ldauu=[ldauu] * len(nio))
        _verify_hubbard_parameters(new_calc)
        ldauu = new_calc.list_float_params["ldauu"]
        if ldauu is None:
            assert True
        else:
            assert (np.zeros(len(nio)) == ldauu).all()

    @staticmethod
    @pytest.mark.parametrize("ldauj", range(9, 12))
    def test_should_set_ldauj_to_zero(nio: ase.Atoms, calc: Vasp, ldauj: int):
        new_calc = deepcopy(calc)
        new_calc.set(ldauj=[ldauj] * len(nio))
        _verify_hubbard_parameters(new_calc)
        ldauj = new_calc.list_float_params["ldauj"]
        if ldauj is None:
            assert True
        else:
            assert (np.zeros(len(nio)) == ldauj).all()

    @staticmethod
    @pytest.mark.parametrize("lorbit", range(5))
    def test_should_set_lorbit_greater_or_equal_to_than_eleven(
        calc: Vasp, lorbit: int
    ):
        new_calc = deepcopy(calc)
        new_calc.set(lorbit=lorbit)
        _verify_hubbard_parameters(new_calc)
        assert new_calc.int_params["lorbit"] >= 11

    @staticmethod
    @pytest.mark.parametrize("lmaxmix", range(5))
    def test_should_set_lmaxmix_greater_or_equal_to_than_four(
        calc: Vasp, lmaxmix: int
    ):
        new_calc = deepcopy(calc)
        new_calc.set(lmaxmix=lmaxmix)
        _verify_hubbard_parameters(new_calc)
        assert new_calc.int_params["lmaxmix"] >= 4

    @staticmethod
    @pytest.mark.parametrize("nsw", range(5))
    def test_should_set_nsw_less_than_one(calc: Vasp, nsw: int):
        new_calc = deepcopy(calc)
        new_calc.set(nsw=nsw)
        _verify_hubbard_parameters(new_calc)
        assert new_calc.int_params["nsw"] <= 1

    @staticmethod
    @pytest.mark.parametrize("index", range(3))
    def test_should_set_ldauluj_none(calc: Vasp, nio: ase.Atoms, index):
        new_calc = deepcopy(calc)
        _configure_for_hubbard(new_calc, nio, index)
        assert new_calc.dict_params["ldau_luj"] is None
