# Input Formats

## Molecule CSV

The first workflow accepts a CSV file with exactly these required columns:

```csv
id,smiles
caffeine,Cn1cnc2n(C)c(=O)n(C)c(=O)c12
aspirin,CC(=O)Oc1ccccc1C(=O)O
```

## Required Columns

| Column | Meaning |
| --- | --- |
| `id` | A stable molecule identifier used in outputs and reports. |
| `smiles` | A SMILES string parsed by RDKit. |

## Common Validation Problems

| Problem | What Open Drug Lab does |
| --- | --- |
| Missing `id` column | Stops during validation. |
| Missing `smiles` column | Stops during validation. |
| Blank row | Ignores the row. |
| Blank molecule id | Records the row in `invalid_molecules.csv`. |
| Invalid SMILES | Records the row in `invalid_molecules.csv`. |
| Duplicate canonical SMILES | Adds an informational flag. |
| Multi-fragment SMILES | Adds a salt/mixture review flag. |

## Why CSV First

CSV keeps the MVP easy to inspect, teach, and test. SDF support is planned for a
future release once the report/provenance layer is stable.
