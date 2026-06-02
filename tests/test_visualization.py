from opendruglab.visualization import write_molecule_grid


def test_write_molecule_grid_skips_empty_descriptor_list(tmp_path) -> None:
    output = tmp_path / "grid.svg"

    written = write_molecule_grid(output, [])

    assert written is False
    assert not output.exists()
