# Demo Report

The v0.2 demo is designed to prove the complete local workflow:

```bash
conda env create -f environment.yml
conda activate open-drug-lab
odl validate workflows/molecule_screen.yaml
odl run workflows/molecule_screen.yaml
```

The run creates a timestamped directory under `runs/`.

## Expected Artifacts

| Artifact | Purpose |
| --- | --- |
| `report.html` | Beginner-readable report with descriptors, flags, provenance, and sources. |
| `molecule_grid.svg` | Visual grid of the valid molecules parsed by RDKit. |
| `manifest.yaml` | Human-readable provenance record. |
| `manifest.json` | Automation-friendly provenance record. |
| `descriptors.csv` | Descriptor table for valid molecules. |
| `flags.csv` | Educational screening flags. |
| `invalid_molecules.csv` | Rows RDKit could not parse. |
| `cleaned_molecules.csv` | Canonical SMILES output. |
| `logs/run.log` | Minimal run log. |

## Demo Molecules

The default demo uses familiar small molecules such as caffeine, aspirin,
acetaminophen, ibuprofen, benzene, and ethanol. It also includes one intentionally
invalid SMILES row so users can see how validation failures are reported.

## What the Demo Does Not Mean

The report is not a claim that any molecule is safe, effective, synthesizable,
or clinically useful. It is a reproducible teaching artifact for learning how
basic cheminformatics descriptors and simple flags are generated.
