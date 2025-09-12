from typer.testing import CliRunner

from ..cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Show available SGN elements" in result.stdout


def test_cli_display_all_elements():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "NullSink" in result.stdout


def test_cli_display_element():
    result = runner.invoke(app, ["NullSink"])
    assert result.exit_code == 0
    assert "NullSink" in result.stdout
    assert "base" in result.stdout
    assert "sink" in result.stdout


def test_cli_display_missing_element():
    result = runner.invoke(app, ["NotAnElement"])
    assert "no such element or plugin" in result.stdout


def test_cli_display_plugin():
    result = runner.invoke(app, ["base"])
    assert result.exit_code == 0
    assert "base" in result.stdout
    assert "Description" in result.stdout
    assert "License" in result.stdout
    assert "NullSink" in result.stdout
