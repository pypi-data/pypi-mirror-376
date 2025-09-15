from typer.testing import CliRunner
from tf_tagguard.cli import app

runner = CliRunner()

def test_cli_missing_file():
    result = runner.invoke(app, ["nonexistent.json", "-r", "Name"])
    assert result.exit_code != 0
