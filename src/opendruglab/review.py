from __future__ import annotations

import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import (
    DescriptorRecord,
    InvalidMoleculeRecord,
    MoleculeRecord,
    ReviewedMoleculeRecord,
    ReviewFlagRecord,
    ReviewSummary,
)
from .report import render_review_report
from .workflow import (
    WorkflowError,
    package_versions,
    read_molecules,
    rule_flags,
    sha256_file,
    write_csv,
    write_json,
)


@dataclass
class ReviewResult:
    output_dir: Path
    summary: ReviewSummary


def review_molecule_csv(
    input_path: Path,
    output_dir: Path | None = None,
) -> ReviewResult:
    try:
        from rdkit import Chem
    except ImportError as exc:
        raise WorkflowError(
            "The review workflow requires RDKit. Install with "
            '`python -m pip install -e ".[chem]"` or use a conda environment '
            "with rdkit."
        ) from exc

    records = read_molecules(input_path)
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    review_dir = output_dir or Path("reviews") / run_id
    review_dir.mkdir(parents=True, exist_ok=True)

    reviewed: list[ReviewedMoleculeRecord] = []
    descriptors: list[DescriptorRecord] = []
    flags: list[ReviewFlagRecord] = []
    invalid: list[InvalidMoleculeRecord] = []
    seen: dict[str, str] = {}

    for record in records:
        if not record.molecule_id:
            invalid.append(
                InvalidMoleculeRecord(
                    molecule_id="",
                    smiles=record.smiles,
                    reason="Missing molecule id.",
                )
            )
            flags.append(_missing_id_flag(record))
            continue

        mol = Chem.MolFromSmiles(record.smiles)
        if mol is None:
            invalid.append(
                InvalidMoleculeRecord(
                    molecule_id=record.molecule_id,
                    smiles=record.smiles,
                    reason="RDKit could not parse this SMILES string.",
                )
            )
            flags.append(_invalid_smiles_flag(record))
            continue

        canonical = Chem.MolToSmiles(mol, canonical=True)
        descriptor = _descriptor_record(record, canonical, mol)
        descriptors.append(descriptor)

        molecule_flags = [
            _review_flag(record, canonical, item)
            for item in rule_flags(descriptor)
        ]
        molecule_flags.extend(_fragment_flags(record, canonical))
        molecule_flags.extend(_standardization_flags(record, canonical))
        if canonical in seen:
            molecule_flags.append(
                ReviewFlagRecord(
                    molecule_id=record.molecule_id,
                    smiles=record.smiles,
                    canonical_smiles=canonical,
                    category="duplicate",
                    severity="warning",
                    message=(
                        "Duplicate canonical SMILES also seen in "
                        f"{seen[canonical]}."
                    ),
                    explanation=(
                        "Duplicate molecules can overweight a dataset, skew simple "
                        "summaries, or hide accidental repeated rows."
                    ),
                )
            )
        else:
            seen[canonical] = record.molecule_id

        flags.extend(molecule_flags)
        reviewed.append(
            ReviewedMoleculeRecord(
                molecule_id=record.molecule_id,
                input_smiles=record.smiles,
                canonical_smiles=canonical,
                status="reviewed",
                warning_count=sum(
                    1 for flag in molecule_flags if flag.severity == "warning"
                ),
                info_count=sum(1 for flag in molecule_flags if flag.severity == "info"),
            )
        )

    summary = _build_summary(
        input_path=input_path,
        output_dir=review_dir,
        records=records,
        reviewed=reviewed,
        invalid=invalid,
        flags=flags,
    )
    manifest = _build_review_manifest(
        input_path=input_path,
        run_id=run_id,
        summary=summary,
    )

    write_csv(review_dir / "reviewed_molecules.csv", reviewed)
    write_csv(review_dir / "review_flags.csv", flags)
    write_csv(review_dir / "invalid_molecules.csv", invalid)
    write_json(review_dir / "review_summary.json", summary.model_dump())
    write_json(review_dir / "review_manifest.json", manifest)
    render_review_report(
        review_dir / "review.html",
        title="Molecule Dataset Review",
        summary=summary,
        flags=flags,
        invalid=invalid,
        reviewed=reviewed,
        manifest=manifest,
    )
    return ReviewResult(output_dir=review_dir, summary=summary)


def _descriptor_record(
    record: MoleculeRecord,
    canonical: str,
    mol: Any,
) -> DescriptorRecord:
    from rdkit.Chem import QED, Crippen, Descriptors, Lipinski, rdMolDescriptors

    return DescriptorRecord(
        molecule_id=record.molecule_id,
        input_smiles=record.smiles,
        canonical_smiles=canonical,
        molecular_weight=round(float(Descriptors.MolWt(mol)), 3),
        clogp=round(float(Crippen.MolLogP(mol)), 3),
        tpsa=round(float(rdMolDescriptors.CalcTPSA(mol)), 3),
        hbd=int(Lipinski.NumHDonors(mol)),
        hba=int(Lipinski.NumHAcceptors(mol)),
        rotatable_bonds=int(Lipinski.NumRotatableBonds(mol)),
        ring_count=int(rdMolDescriptors.CalcNumRings(mol)),
        formal_charge=int(sum(atom.GetFormalCharge() for atom in mol.GetAtoms())),
        qed=round(float(QED.qed(mol)), 3),
    )


def _review_flag(
    record: MoleculeRecord,
    canonical: str,
    flag: Any,
) -> ReviewFlagRecord:
    return ReviewFlagRecord(
        molecule_id=record.molecule_id,
        smiles=record.smiles,
        canonical_smiles=canonical,
        category=flag.flag,
        severity=flag.severity,
        message=flag.message,
        explanation=_flag_explanation(flag.flag),
    )


def _fragment_flags(record: MoleculeRecord, canonical: str) -> list[ReviewFlagRecord]:
    if "." not in canonical:
        return []
    return [
        ReviewFlagRecord(
            molecule_id=record.molecule_id,
            smiles=record.smiles,
            canonical_smiles=canonical,
            category="salt_or_mixture",
            severity="warning",
            message="Canonical SMILES contains multiple fragments.",
            explanation=(
                "Multiple fragments often indicate salts, counterions, solvents, "
                "or mixtures. Decide whether to keep, strip, or separately review "
                "fragments before comparing molecules."
            ),
        )
    ]


def _standardization_flags(
    record: MoleculeRecord,
    canonical: str,
) -> list[ReviewFlagRecord]:
    try:
        from rdkit.Chem.MolStandardize import rdMolStandardize
    except ImportError:
        return [
            ReviewFlagRecord(
                molecule_id=record.molecule_id,
                smiles=record.smiles,
                canonical_smiles=canonical,
                category="standardization_validation_unavailable",
                severity="info",
                message="RDKit MolStandardize validation was not available.",
                explanation=(
                    "The dataset can still be parsed, but this environment could "
                    "not run RDKit's standardization validation checks."
                ),
            )
        ]

    messages = rdMolStandardize.ValidateSmiles(record.smiles)
    return [
        ReviewFlagRecord(
            molecule_id=record.molecule_id,
            smiles=record.smiles,
            canonical_smiles=canonical,
            category="rdkit_standardization",
            severity=(
                "warning" if message.startswith(("ERROR", "WARNING")) else "info"
            ),
            message=message,
            explanation=(
                "RDKit standardization validation found a structure feature worth "
                "reviewing before downstream interpretation."
            ),
        )
        for message in messages
    ]


def _missing_id_flag(record: MoleculeRecord) -> ReviewFlagRecord:
    return ReviewFlagRecord(
        molecule_id="",
        smiles=record.smiles,
        category="missing_id",
        severity="error",
        message="Row has a SMILES value but no molecule id.",
        explanation=(
            "Stable molecule IDs are needed for review, deduplication, reports, "
            "and downstream traceability."
        ),
    )


def _invalid_smiles_flag(record: MoleculeRecord) -> ReviewFlagRecord:
    return ReviewFlagRecord(
        molecule_id=record.molecule_id,
        smiles=record.smiles,
        category="invalid_smiles",
        severity="error",
        message="RDKit could not parse this SMILES string.",
        explanation=(
            "Invalid SMILES cannot be reviewed with descriptor or structure rules. "
            "Fix the input string or remove the row before screening."
        ),
    )


def _flag_explanation(flag: str) -> str:
    explanations = {
        "mw_gt_500": (
            "High molecular weight can reduce oral drug-likeness under simple "
            "heuristic rules."
        ),
        "clogp_gt_5": (
            "High cLogP can indicate poor aqueous solubility or high "
            "lipophilicity."
        ),
        "hbd_gt_5": (
            "Many hydrogen bond donors can affect permeability under simple rules."
        ),
        "hba_gt_10": (
            "Many hydrogen bond acceptors can affect permeability under simple "
            "rules."
        ),
        "rotatable_bonds_gt_10": (
            "Highly flexible molecules can be harder to optimize or compare."
        ),
        "formal_charge": (
            "Large formal charge can affect handling, salts, and interpretation."
        ),
        "no_basic_rule_flags": (
            "No simple threshold fired; this is not evidence of safety or efficacy."
        ),
    }
    return explanations.get(
        flag,
        "Review this signal before making downstream assumptions.",
    )


def _build_summary(
    *,
    input_path: Path,
    output_dir: Path,
    records: list[MoleculeRecord],
    reviewed: list[ReviewedMoleculeRecord],
    invalid: list[InvalidMoleculeRecord],
    flags: list[ReviewFlagRecord],
) -> ReviewSummary:
    duplicate_ids = {
        flag.molecule_id for flag in flags if flag.category == "duplicate"
    }
    salt_ids = {
        flag.molecule_id for flag in flags if flag.category == "salt_or_mixture"
    }
    return ReviewSummary(
        input_file=str(input_path),
        output_dir=str(output_dir),
        total_rows=len(records),
        reviewed_molecules=len(reviewed),
        invalid_molecules=len(invalid),
        duplicate_molecules=len(duplicate_ids),
        salt_or_mixture_molecules=len(salt_ids),
        warning_flags=sum(1 for flag in flags if flag.severity == "warning"),
        info_flags=sum(1 for flag in flags if flag.severity == "info"),
        error_flags=sum(1 for flag in flags if flag.severity == "error"),
    )


def _build_review_manifest(
    *,
    input_path: Path,
    run_id: str,
    summary: ReviewSummary,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "workflow": "molecule_dataset_review",
        "input": {
            "molecules": str(input_path),
            "sha256": sha256_file(input_path),
        },
        "summary": summary.model_dump(),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": package_versions(
                ["opendruglab", "rdkit", "jinja2", "pydantic", "pyyaml"]
            ),
        },
        "disclaimer": (
            "Dataset review is an educational quality-control aid. Flags are "
            "not toxicity predictions, activity predictions, or rejection rules."
        ),
    }
