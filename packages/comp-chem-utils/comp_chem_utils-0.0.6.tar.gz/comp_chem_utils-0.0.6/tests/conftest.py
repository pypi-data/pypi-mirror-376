from pathlib import Path
from typing import Any

import ase
from ase.build import molecule
from ase.calculators.calculator import Calculator
from ase.calculators.emt import EMT
from ase.optimize.bfgs import BFGS
from ase.optimize.optimize import Optimizer
import numpy as np
import pytest

from ccu.structure.geometry import MolecularOrientation


@pytest.fixture(name="structure")
def fixture_structure() -> ase.Atoms:
    return ase.Atoms(
        "O2Cu",
        positions=[
            [0, 0, 0],
            [2, 0, 0],
            [1, 1, 0],
        ],
        tags=[1, 1, 2],
        cell=5 * np.eye(3),
    )


@pytest.fixture(name="orientation", params=[[0.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
def fixture_orientation(request) -> MolecularOrientation:
    axis1 = np.array([1.0, 0.0, 0.0])
    axis2 = np.array(request.param)
    return MolecularOrientation((axis1, axis2), "")


WORKFLOWS = """
#########
WORKFLOWS
#########
"""


@pytest.fixture(name="atoms")
def fixture_atoms(calculator: Calculator) -> ase.Atoms:
    atoms = molecule("CO2")
    atoms.calc = calculator
    return atoms


@pytest.fixture(name="calculator")
def fixture_calculator(tmp_path: Path) -> Calculator:
    calc = EMT(directory=str(tmp_path))
    return calc


@pytest.fixture(name="trajectory")
def fixture_trajectory(tmp_path: Path) -> Path:
    return Path(tmp_path, "relax.traj")


@pytest.fixture(name="opt", params=[None, BFGS])
def fixture_opt(
    atoms: ase.Atoms,
    trajectory: str,
    request: pytest.FixtureRequest,
) -> Optimizer | None:
    try:
        return request.param(atoms, trajectory=trajectory)
    except:  # noqa: E722
        return None


@pytest.fixture(name="fmax")
def fixture_fmax() -> float:
    return 0.01


@pytest.fixture(name="steps")
def fixture_steps() -> int:
    return 10


@pytest.fixture(name="opt_params")
def fixture_opt_params(
    fmax: float,
    steps: int,
) -> dict[str, Any]:
    return {
        "fmax": fmax,
        "steps": steps,
    }
