import numpy as np
import pytest

from ccu.thermo.chempot import ChemPotDatabase
from ccu.thermo.chempot import calculate

MOLECULES = list(ChemPotDatabase().zpe_data)


class TestChemPotCalculator:
    @staticmethod
    @pytest.fixture(name="molecule", params=MOLECULES)
    def fixture_molecule(request: pytest.FixtureRequest) -> str:
        molecule: str = request.param

        return molecule

    @staticmethod
    @pytest.fixture(name="temperature", params=np.linspace(1, 1000 - 1e-5, 4))
    def fixture_temperature(request: pytest.FixtureRequest) -> float:
        temperature: float = request.param
        return temperature

    @staticmethod
    @pytest.fixture(name="pressure", params=np.linspace(1, 10, 3))
    def fixture_pressure(request: pytest.FixtureRequest) -> float:
        pressure: float = request.param
        return pressure

    @staticmethod
    def test_should_work(
        molecule: str, temperature: float, pressure: float
    ) -> None:
        assert calculate(molecule, temperature, pressure)
