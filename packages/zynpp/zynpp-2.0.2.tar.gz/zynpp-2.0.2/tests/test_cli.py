from typer.testing import CliRunner

from zpp.cli import app


def test_version() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "zpp" in result.stdout


