# Contributing

Thanks for helping make computational drug-discovery workflows easier to learn
and reproduce.

## Principles

- Prefer trusted upstream tools over new scientific implementations.
- Keep workflows local-first and small enough for CI.
- Save provenance for every run.
- Avoid medical, clinical, efficacy, or safety claims.
- Make failure messages useful for beginners.

## Good First Issues

- Add descriptor explanations to the HTML report.
- Add more safe demo molecules.
- Improve invalid SMILES messages.
- Add report screenshots to the README.
- Add a Datamol standardization option.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```
