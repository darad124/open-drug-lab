from pathlib import Path

from opendruglab.models import (
    InvalidMoleculeRecord,
    MoleculeRecord,
    ReviewedMoleculeRecord,
    ReviewFlagRecord,
)
from opendruglab.review import _build_summary


def test_build_summary_counts_review_categories(tmp_path) -> None:
    flags = [
        ReviewFlagRecord(
            molecule_id="aspirin-copy",
            smiles="CC(=O)Oc1ccccc1C(=O)O",
            canonical_smiles="CC(=O)Oc1ccccc1C(=O)O",
            category="duplicate",
            severity="warning",
            message="Duplicate canonical SMILES.",
            explanation="Duplicates can skew summaries.",
        ),
        ReviewFlagRecord(
            molecule_id="salt",
            smiles="CCO.Cl",
            canonical_smiles="CCO.Cl",
            category="salt_or_mixture",
            severity="warning",
            message="Multiple fragments.",
            explanation="Fragments need review.",
        ),
        ReviewFlagRecord(
            molecule_id="ethanol",
            smiles="CCO",
            canonical_smiles="CCO",
            category="no_basic_rule_flags",
            severity="info",
            message="No simple rule flags.",
            explanation="Not a safety claim.",
        ),
    ]

    summary = _build_summary(
        input_path=Path("molecules.csv"),
        output_dir=tmp_path / "review",
        records=[
            MoleculeRecord(molecule_id="ethanol", smiles="CCO"),
            MoleculeRecord(molecule_id="aspirin-copy", smiles="CC(=O)Oc1ccccc1C(=O)O"),
            MoleculeRecord(molecule_id="salt", smiles="CCO.Cl"),
            MoleculeRecord(molecule_id="bad", smiles="not_a_smiles"),
        ],
        reviewed=[
            ReviewedMoleculeRecord(
                molecule_id="ethanol",
                input_smiles="CCO",
                canonical_smiles="CCO",
                status="reviewed",
                warning_count=0,
                info_count=1,
            )
        ],
        invalid=[
            InvalidMoleculeRecord(
                molecule_id="bad",
                smiles="not_a_smiles",
                reason="RDKit could not parse this SMILES string.",
            )
        ],
        flags=flags,
    )

    assert summary.total_rows == 4
    assert summary.reviewed_molecules == 1
    assert summary.invalid_molecules == 1
    assert summary.duplicate_molecules == 1
    assert summary.salt_or_mixture_molecules == 1
    assert summary.warning_flags == 2
    assert summary.info_flags == 1
