from __future__ import annotations

import csv
import hashlib
import platform
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import yaml

from .models import (
    DescriptorRecord,
    FlagRecord,
    InvalidMoleculeRecord,
    MoleculeRecord,
    WorkflowConfig,
)
from .report import render_report


class WorkflowError(RuntimeError):
    """Raised when a workflow cannot run."""


@dataclass
class WorkflowResult:
    run_id: str
    run_dir: Path
    valid_count: int
    invalid_count: int


def load_workflow(path: Path) -> WorkflowConfig:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return WorkflowConfig.model_validate(data)


def run_molecule_screen(config_path: Path) -> WorkflowResult:
    config = load_workflow(config_path)
    root = (
        config_path.parent.parent
        if config_path.parent.name == "workflows"
        else Path.cwd()
    )
    molecules_path = _resolve_path(root, config.inputs.molecules)
    runs_dir = _resolve_path(root, config.outputs.runs_dir)

    records = read_molecules(molecules_path)
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / run_id
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    descriptors, flags, invalid = screen_molecules(records)
    write_csv(run_dir / "descriptors.csv", descriptors)
    write_csv(run_dir / "flags.csv", flags)
    write_csv(run_dir / "invalid_molecules.csv", invalid)
    write_cleaned_molecules(run_dir / "cleaned_molecules.csv", descriptors)
    manifest = build_manifest(
        config=config,
        config_path=config_path,
        molecules_path=molecules_path,
        run_id=run_id,
        descriptors=descriptors,
        flags=flags,
        invalid=invalid,
    )
    write_yaml(run_dir / "manifest.yaml", manifest)
    (logs_dir / "run.log").write_text(
        f"Open Drug Lab run {run_id}\n"
        f"Valid molecules: {len(descriptors)}\n"
        f"Invalid molecules: {len(invalid)}\n",
        encoding="utf-8",
    )
    render_report(
        run_dir / "report.html",
        title=config.settings.report_title,
        descriptors=descriptors,
        flags=flags,
        invalid=invalid,
        manifest=manifest,
    )
    return WorkflowResult(
        run_id=run_id,
        run_dir=run_dir,
        valid_count=len(descriptors),
        invalid_count=len(invalid),
    )


def read_molecules(path: Path) -> list[MoleculeRecord]:
    if not path.exists():
        raise WorkflowError(f"Molecule input file does not exist: {path}")

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"id", "smiles"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise WorkflowError(
                f"Molecule CSV must include columns: {', '.join(sorted(required))}"
            )
        return [
            MoleculeRecord(
                molecule_id=(row.get("id") or "").strip(),
                smiles=(row.get("smiles") or "").strip(),
            )
            for row in reader
            if (row.get("id") or "").strip() or (row.get("smiles") or "").strip()
        ]


def screen_molecules(
    records: list[MoleculeRecord],
) -> tuple[list[DescriptorRecord], list[FlagRecord], list[InvalidMoleculeRecord]]:
    try:
        from rdkit import Chem
        from rdkit.Chem import (
            QED,
            Crippen,
            Descriptors,
            Lipinski,
            rdMolDescriptors,
        )
    except ImportError as exc:
        raise WorkflowError(
            "The molecule_screen workflow requires RDKit. Install with "
            '`python -m pip install -e ".[chem]"` or use a conda environment '
            "with rdkit."
        ) from exc

    descriptors: list[DescriptorRecord] = []
    flags: list[FlagRecord] = []
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
            continue

        canonical = Chem.MolToSmiles(mol, canonical=True)
        descriptor = DescriptorRecord(
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
        descriptors.append(descriptor)
        flags.extend(rule_flags(descriptor))

        if "." in canonical:
            flags.append(
                FlagRecord(
                    molecule_id=record.molecule_id,
                    flag="mixture_or_salt",
                    severity="warning",
                    message=(
                        "Canonical SMILES contains multiple fragments. "
                        "Review salt/mixture handling before interpretation."
                    ),
                )
            )
        if canonical in seen:
            flags.append(
                FlagRecord(
                    molecule_id=record.molecule_id,
                    flag="duplicate",
                    severity="info",
                    message=(
                        "Duplicate canonical SMILES also seen in "
                        f"{seen[canonical]}."
                    ),
                )
            )
        else:
            seen[canonical] = record.molecule_id

    return descriptors, flags, invalid


def rule_flags(record: DescriptorRecord) -> list[FlagRecord]:
    flags: list[FlagRecord] = []
    checks = [
        (record.molecular_weight > 500, "mw_gt_500", "Molecular weight is above 500."),
        (record.clogp > 5, "clogp_gt_5", "cLogP is above 5."),
        (record.hbd > 5, "hbd_gt_5", "Hydrogen bond donors are above 5."),
        (record.hba > 10, "hba_gt_10", "Hydrogen bond acceptors are above 10."),
        (
            record.rotatable_bonds > 10,
            "rotatable_bonds_gt_10",
            "Rotatable bond count is above 10.",
        ),
        (
            abs(record.formal_charge) > 1,
            "formal_charge",
            "Formal charge magnitude is above 1.",
        ),
    ]
    for failed, flag, message in checks:
        if failed:
            flags.append(
                FlagRecord(
                    molecule_id=record.molecule_id,
                    flag=flag,
                    severity="warning",
                    message=message,
                )
            )
    if not flags:
        flags.append(
            FlagRecord(
                molecule_id=record.molecule_id,
                flag="no_basic_rule_flags",
                severity="info",
                message="No simple Lipinski-style rule flags were triggered.",
            )
        )
    return flags


def build_manifest(
    *,
    config: WorkflowConfig,
    config_path: Path,
    molecules_path: Path,
    run_id: str,
    descriptors: list[DescriptorRecord],
    flags: list[FlagRecord],
    invalid: list[InvalidMoleculeRecord],
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "workflow": config.workflow,
        "workflow_name": config.name,
        "config_path": str(config_path),
        "input": {
            "molecules": str(molecules_path),
            "sha256": sha256_file(molecules_path),
        },
        "settings": config.settings.model_dump(),
        "counts": {
            "valid_molecules": len(descriptors),
            "invalid_molecules": len(invalid),
            "flags": len(flags),
        },
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": package_versions(
                ["opendruglab", "rdkit", "jinja2", "pydantic", "pyyaml"]
            ),
        },
        "disclaimer": (
            "Educational screening only. Outputs are not medical advice, safety "
            "claims, toxicity predictions, or clinical decision support."
        ),
    }


def write_csv(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    data = [row.model_dump() for row in rows]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)


def write_cleaned_molecules(path: Path, descriptors: list[DescriptorRecord]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "canonical_smiles"])
        writer.writeheader()
        for row in descriptors:
            writer.writerow(
                {"id": row.molecule_id, "canonical_smiles": row.canonical_smiles}
            )


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def package_versions(names: list[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_path(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else (root / value).resolve()
