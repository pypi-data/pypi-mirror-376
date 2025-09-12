from click.testing import CliRunner

from ccu._cli._main import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.output == ""
    assert result.exit_code == 0
