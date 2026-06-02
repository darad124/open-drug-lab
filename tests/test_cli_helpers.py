from typer.testing import CliRunner

from opendruglab.cli import _write_demo_file, app


def test_cli_help_builds_command_tree() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "validate" in result.output


def test_write_demo_file_preserves_existing_without_force(tmp_path) -> None:
    output = tmp_path / "demo.csv"
    output.write_text("existing", encoding="utf-8")

    _write_demo_file(output, "new", force=False)

    assert output.read_text(encoding="utf-8") == "existing"


def test_write_demo_file_overwrites_with_force(tmp_path) -> None:
    output = tmp_path / "demo.csv"
    output.write_text("existing", encoding="utf-8")

    _write_demo_file(output, "new", force=True)

    assert output.read_text(encoding="utf-8") == "new"
