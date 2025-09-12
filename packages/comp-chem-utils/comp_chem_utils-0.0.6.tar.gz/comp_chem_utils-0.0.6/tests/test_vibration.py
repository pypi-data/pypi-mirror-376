from collections.abc import Generator
from pathlib import Path

from ase.atoms import Atoms
from ase.vibrations.data import VibrationsData
from numpy.testing import assert_array_equal
import pytest

from ccu import SETTINGS
from ccu.workflows.vibration import run_vibration


@pytest.fixture(name="name")
def fixture_name() -> str:
    return "vib"


@pytest.fixture(name="run_vibration", autouse=True)
def fixture_run_vibration(
    atoms: Atoms,
    name: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[Atoms, VibrationsData], None, None]:
    with monkeypatch.context() as mp:
        mp.setattr(SETTINGS, "LOG_FILE", Path(tmp_path, "vib.log"))
        yield run_vibration(atoms, name=name)


class TestIO:
    @staticmethod
    def test_should_write_summary_file(tmp_path: Path, name: str) -> None:
        assert Path(tmp_path, f"{name}.log").exists()

    @staticmethod
    def test_should_write_vibrations_data_file(
        tmp_path: Path, name: str
    ) -> None:
        assert Path(tmp_path, f"{name}.json").exists()


class TestReadableResults:
    @staticmethod
    @pytest.fixture(
        name="loaded_vib_data",
    )
    def fixture_loaded_vib_data(tmp_path: Path, name: str) -> VibrationsData:
        loaded_vib_data: VibrationsData = VibrationsData.read(  # type: ignore[attr-defined]
            Path(tmp_path, f"{name}.json")
        )
        return loaded_vib_data

    @staticmethod
    def test_should_write_vibration_data_with_all_calculator_results(
        run_vibration: tuple[Atoms, VibrationsData],
        loaded_vib_data: VibrationsData,
    ) -> None:
        vib_atoms, vib_data = run_vibration
        assert loaded_vib_data.get_atoms() == vib_atoms
        assert_array_equal(
            loaded_vib_data.get_hessian(), vib_data.get_hessian()
        )
        assert_array_equal(
            loaded_vib_data.get_indices(), vib_data.get_indices()
        )
