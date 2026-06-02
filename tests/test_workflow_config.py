from pathlib import Path

from opendruglab.workflow import load_workflow, sha256_file


def test_load_demo_workflow() -> None:
    config = load_workflow(Path("workflows/molecule_screen.yaml"))

    assert config.workflow == "molecule_screen"
    assert config.inputs.molecules == Path("examples/molecules/demo_molecules.csv")
    assert config.settings.standardize == "conservative"


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("open drug lab\n", encoding="utf-8")

    first = sha256_file(sample)
    second = sha256_file(sample)

    assert first == second
    assert len(first) == 64
