# Release Process

Open Drug Lab releases should be small, reproducible, and conservative.

## Before a Release

1. Run `ruff check .`.
2. Run `pytest`.
3. Run the demo workflow in a Python 3.10-3.12 RDKit environment.
4. Confirm `report.html`, `manifest.yaml`, and `manifest.json` are generated.
5. Review report language for scientific overclaiming.
6. Update `CHANGELOG.md`.

## Versioning

Use semantic versioning:

- Patch: bug fixes and report copy improvements.
- Minor: new workflows, outputs, or supported input types.
- Major: breaking workflow YAML or output schema changes.

## Release Artifacts

Attach or link:

- generated demo report
- example `manifest.yaml`
- example `descriptors.csv`
- known limitations
