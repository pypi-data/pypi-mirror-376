from pathlib import Path

from click.testing import CliRunner
import pytest

from ccu._cli._main import main


@pytest.fixture(name="cache")
def fixture_cache(datadir: Path) -> Path:
    cache = datadir.joinpath("test.fancy")
    return cache


@pytest.fixture(name="data")
def fixture_data(datadir: Path) -> Path:
    data = datadir.joinpath("feddata.json")
    return data


@pytest.mark.gui
class TestGUI:
    @staticmethod
    def test_should_run_with_cache(cache: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "-vv",
                "--log-level",
                "DEBUG",
                "--log-file",
                "ccu.log",
                "fed",
                "--cache",
                str(cache),
            ],
        )
        assert result.exit_code == 0

    @staticmethod
    def test_should_run_without_cache() -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "-vv",
                "--log-level",
                "DEBUG",
                "--log-file",
                "ccu.log",
                "fed",
            ],
        )
        assert result.exit_code == 0

    @staticmethod
    def test_should_run_with_data(data: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "-vv",
                "--log-level",
                "DEBUG",
                "--log-file",
                "ccu.log",
                "fed",
                "--data",
                str(data),
            ],
        )
        assert result.exit_code == 0
