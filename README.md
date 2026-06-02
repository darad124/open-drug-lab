# Open Drug Lab

Open Drug Lab is a local-first educational workflow kit for reproducible
computational drug-discovery learning.

It does **not** discover drugs, make medical claims, or replace expert
scientific judgment. It wraps trusted chemistry tooling into small workflows that
save provenance, explain assumptions, and generate beginner-readable reports.

## Why This Exists

Great tools already exist: RDKit, OpenMM, DeepChem, Datamol, OpenFE, Meeko, and
AutoDock Vina. The hard part for learners and small labs is often getting a
complete workflow to run, understanding what happened, and preserving enough
metadata to reproduce the result.

Open Drug Lab focuses on that layer:

- one-command local workflows
- explicit input validation
- reproducible run manifests
- beginner-readable HTML reports
- CI-tested examples
- conservative scientific disclaimers

## Quick Start

For the chemistry workflow, use Python 3.10-3.12. The easiest path is a conda
environment because RDKit support for very new Python versions can lag.

```bash
conda env create -f environment.yml
conda activate open-drug-lab
```

Or install with pip in a compatible Python environment:

```bash
python -m pip install -e ".[chem]"
```

Run the demo workflow:

```bash
odl run workflows/molecule_screen.yaml
```

Outputs are written to `runs/<run_id>/`:

```text
report.html
manifest.yaml
descriptors.csv
flags.csv
invalid_molecules.csv
cleaned_molecules.csv
logs/run.log
```

## Example Workflow

```yaml
name: demo molecule screen
workflow: molecule_screen
inputs:
  molecules: examples/molecules/demo_molecules.csv
outputs:
  runs_dir: runs
settings:
  standardize: conservative
  report_title: Demo Molecule Screen
```

See [Input Formats](docs/input-formats.md) for the expected molecule CSV shape
and common validation failures.

## Scientific Scope

Open Drug Lab outputs are educational screening artifacts. Descriptor flags such
as Lipinski-style alerts are not efficacy, safety, toxicity, or clinical
predictions. Results should be reviewed by qualified experts before any research
or operational decision.

## Development

Install dev dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting:

```bash
ruff check .
```

See [Release Process](docs/release-process.md) for maintainer release steps.

## Current MVP Boundary

v0.1 intentionally starts with molecule cleanup, descriptors, simple educational
rule flags, provenance, and reports. Docking, molecular dynamics, and ADMET
model predictions are planned as optional future modules, not as initial claims.
