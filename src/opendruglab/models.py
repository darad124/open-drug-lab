from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class WorkflowInputs(BaseModel):
    molecules: Path


class WorkflowOutputs(BaseModel):
    runs_dir: Path = Path("runs")


class WorkflowSettings(BaseModel):
    standardize: Literal["conservative", "none"] = "conservative"
    report_title: str = "Molecule Screen"


class WorkflowConfig(BaseModel):
    name: str
    workflow: Literal["molecule_screen"]
    inputs: WorkflowInputs
    outputs: WorkflowOutputs = Field(default_factory=WorkflowOutputs)
    settings: WorkflowSettings = Field(default_factory=WorkflowSettings)


class MoleculeRecord(BaseModel):
    molecule_id: str
    smiles: str


class DescriptorRecord(BaseModel):
    molecule_id: str
    input_smiles: str
    canonical_smiles: str
    molecular_weight: float
    clogp: float
    tpsa: float
    hbd: int
    hba: int
    rotatable_bonds: int
    ring_count: int
    formal_charge: int
    qed: float


class FlagRecord(BaseModel):
    molecule_id: str
    flag: str
    severity: Literal["info", "warning"]
    message: str


class InvalidMoleculeRecord(BaseModel):
    molecule_id: str
    smiles: str
    reason: str


class ReviewFlagRecord(BaseModel):
    molecule_id: str
    smiles: str
    canonical_smiles: str | None = None
    category: str
    severity: Literal["info", "warning", "error"]
    message: str
    explanation: str


class ReviewedMoleculeRecord(BaseModel):
    molecule_id: str
    input_smiles: str
    canonical_smiles: str
    status: Literal["reviewed"]
    warning_count: int
    info_count: int


class ReviewSummary(BaseModel):
    input_file: str
    output_dir: str
    total_rows: int
    reviewed_molecules: int
    invalid_molecules: int
    duplicate_molecules: int
    salt_or_mixture_molecules: int
    warning_flags: int
    info_flags: int
    error_flags: int
