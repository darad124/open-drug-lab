from __future__ import annotations

from pathlib import Path

from .models import DescriptorRecord


def write_molecule_grid(
    path: Path,
    descriptors: list[DescriptorRecord],
    *,
    max_molecules: int = 12,
) -> bool:
    """Write an SVG molecule grid for valid descriptors.

    Returns True when a grid was written. RDKit is imported lazily so base
    package tests can run without chemistry dependencies.
    """
    if not descriptors:
        return False

    from rdkit import Chem
    from rdkit.Chem import Draw

    mols = []
    legends = []
    for row in descriptors[:max_molecules]:
        mol = Chem.MolFromSmiles(row.canonical_smiles)
        if mol is None:
            continue
        mols.append(mol)
        legends.append(row.molecule_id)

    if not mols:
        return False

    svg = Draw.MolsToGridImage(
        mols,
        molsPerRow=3,
        subImgSize=(260, 180),
        legends=legends,
        useSVG=True,
    )
    path.write_text(str(svg), encoding="utf-8")
    return True
