from typer.testing import CliRunner

from opendruglab.cli import _write_demo_file, app


def test_cli_help_builds_command_tree() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "validate" in result.output
    assert "review" in result.output


def test_review_command_explains_missing_rdkit(tmp_path) -> None:
    molecules = tmp_path / "molecules.csv"
    molecules.write_text("id,smiles\nethanol,CCO\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["review", str(molecules)])

    assert result.exit_code == 1
    assert "requires RDKit" in result.output


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
