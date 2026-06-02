# Dataset Review

`odl review` audits a molecule CSV before downstream screening. It is meant for
students, educators, and early-stage open-science projects that need to know
whether a molecule list is parseable, duplicated, fragmented, or risky to
over-interpret.

```bash
odl review examples/molecules/demo_molecules.csv
```

To choose the output directory:

```bash
odl review examples/molecules/demo_molecules.csv --output-dir reviews/demo
```

## Outputs

The review writes:

- `review.html`: beginner-readable audit report.
- `review_summary.json`: machine-readable counts and artifact locations.
- `review_manifest.json`: provenance, input checksum, environment, and package versions.
- `review_flags.csv`: all warnings, errors, and information flags.
- `reviewed_molecules.csv`: canonical SMILES and per-molecule flag counts.
- `invalid_molecules.csv`: rows RDKit could not parse or trace.

## What It Checks

The v0.3 review workflow checks:

- missing molecule IDs
- invalid SMILES
- duplicate canonical SMILES
- salts, counterions, solvents, or mixtures represented as multiple fragments
- simple Lipinski-style descriptor thresholds
- RDKit MolStandardize validation messages when available

These checks are quality-control signals. They are not toxicity, activity,
synthesis, safety, or clinical predictions.

## Why This Exists

Many learners start from a CSV copied out of a paper, database, generated model,
or class exercise. The first problem is not docking or machine learning. The
first problem is knowing whether the input list is clean enough to trust.

Open Drug Lab turns that first-mile review into a reproducible artifact with
plain-language explanations and a checksum-backed manifest.
