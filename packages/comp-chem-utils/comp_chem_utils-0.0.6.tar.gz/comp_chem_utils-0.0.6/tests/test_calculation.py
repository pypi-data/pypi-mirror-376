from pathlib import Path
from typing import Any

import ase
from ase.atoms import Atoms
from ase.calculators.calculator import Calculator
from ase.optimize.bfgs import BFGS
from ase.optimize.optimize import Optimizer
from numpy.testing import assert_array_equal
import pytest

from ccu import SETTINGS
from ccu.workflows.calculation import run_calculation


@pytest.fixture(name="run_relaxation", autouse=True)
def fixture_run_relaxation(
    atoms: ase.Atoms, opt: Optimizer | None, opt_params: dict[str, Any]
) -> tuple[Atoms, Optimizer | None]:
    return run_calculation(atoms, opt=opt, **opt_params)


@pytest.mark.parametrize("opt", [None, BFGS], indirect=True)
def test_should_add_energy_to_results(calculator: Calculator) -> None:
    assert "energy" in calculator.results


@pytest.mark.parametrize("opt", [BFGS], indirect=True)
class TestResults:
    @staticmethod
    def test_should_add_force_to_results_if_opt_is_not_none(
        calculator: Calculator,
    ) -> None:
        assert "forces" in calculator.results

    @staticmethod
    def test_should_run_optimizer(opt: Optimizer, steps: int) -> None:
        assert (
            opt.converged(opt.optimizable.get_gradient())
            or opt.nsteps == steps
        )

    @staticmethod
    def test_should_write_restart_file(
        tmp_path: Path, trajectory: str
    ) -> None:
        assert Path(tmp_path, trajectory).exists()


class TestReadableResults:
    @staticmethod
    def test_should_write_output_trajectory_with_all_calculator_results(
        tmp_path: Path, calculator: Calculator
    ) -> None:
        atoms = ase.io.read(Path(tmp_path, SETTINGS.OUTPUT_ATOMS))
        atoms = atoms[0] if isinstance(atoms, list) else atoms
        for key, value in calculator.results.items():
            assert_array_equal(value, atoms.calc.results.get(key))
