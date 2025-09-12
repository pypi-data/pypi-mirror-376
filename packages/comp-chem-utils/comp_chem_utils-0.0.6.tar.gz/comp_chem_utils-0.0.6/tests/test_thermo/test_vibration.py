import contextlib
import logging
from pathlib import Path

from ase.build import molecule
from ase.calculators.emt import EMT
import pytest

from ccu.workflows.vibration import run_vibration


class TestRunVibration:
    @pytest.mark.skipif("sys.version_info < (3, 11)")
    @staticmethod
    def test_should_log_without_errors(tmp_path: Path) -> None:
        atoms = molecule("CO2")
        atoms.calc = EMT()
        file = tmp_path.joinpath("log.txt")
        logging.basicConfig(filename=file, level=logging.DEBUG)
        with file.open(mode="w", encoding="utf-8") as f:
            h = logging.StreamHandler(f)
            root = logging.getLogger()
            root.addHandler(h)
            root.setLevel(logging.DEBUG)
            with contextlib.chdir(tmp_path):
                run_vibration(atoms=atoms)

        with file.open(mode="r", encoding="utf-8") as f:
            lines = f.readlines()
        assert lines
