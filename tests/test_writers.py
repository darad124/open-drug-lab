import json

from opendruglab.workflow import write_json


def test_write_json_creates_pretty_json(tmp_path) -> None:
    output = tmp_path / "manifest.json"

    write_json(output, {"run_id": "demo", "counts": {"valid": 2}})

    assert json.loads(output.read_text(encoding="utf-8"))["run_id"] == "demo"
    assert output.read_text(encoding="utf-8").endswith("\n")
