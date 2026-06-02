# Changelog

All notable changes to Open Drug Lab will be documented here.

## 0.2.0 - Unreleased

### Added

- `odl review` command for molecule CSV dataset audits.
- Review artifacts: HTML report, summary JSON, manifest JSON, flags CSV,
  reviewed molecule CSV, and invalid molecule CSV.
- Dataset review documentation with quality-control scope and safety boundaries.
- Molecule grid SVG generation for chemistry runs.
- Report embedding for generated molecule grids.
- Conda/RDKit CI workflow that runs the demo molecule screen.
- Demo report documentation with expected artifacts.
- Safer `odl init` behavior that preserves files unless `--force` is used.

## 0.1.0 - 2026-06-02

### Added

- `odl run` command for molecule screening workflows.
- `odl validate` command for workflow and molecule CSV validation.
- `odl init` command for creating a runnable demo workspace.
- Molecule descriptor calculation workflow powered by RDKit.
- Educational Lipinski-style rule flags.
- Invalid molecule reporting.
- YAML and JSON run manifests.
- Static HTML reports with descriptor explanations and sources.
- Scientific safety documentation.
- GitHub issue templates and CI.

### Notes

- The first release is educational workflow tooling only.
- Docking, ADMET model prediction, and molecular dynamics are not part of v0.1.
