from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .workflow import WorkflowError, run_molecule_screen

app = typer.Typer(help="Open Drug Lab command line interface.")
console = Console()
CONFIG_ARG = typer.Argument(..., help="Path to a workflow YAML file.")
TARGET_ARG = typer.Argument(help="Directory to initialize.")
DEMO_MOLECULES = """id,smiles
caffeine,Cn1cnc2n(C)c(=O)n(C)c(=O)c12
aspirin,CC(=O)Oc1ccccc1C(=O)O
acetaminophen,CC(=O)Nc1ccc(O)cc1
ibuprofen,CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O
benzene,c1ccccc1
ethanol,CCO
invalid_demo,not_a_smiles
"""
DEMO_WORKFLOW = """name: demo molecule screen
workflow: molecule_screen
inputs:
  molecules: examples/molecules/demo_molecules.csv
outputs:
  runs_dir: runs
settings:
  standardize: conservative
  report_title: Demo Molecule Screen
"""


@app.command()
def run(config: Annotated[Path, CONFIG_ARG]) -> None:
    """Run a workflow and write artifacts to a run directory."""
    try:
        result = run_molecule_screen(config)
    except WorkflowError as exc:
        console.print("[bold red]Workflow failed:[/bold red]")
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc

    table = Table(title="Open Drug Lab run complete")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Run ID", result.run_id)
    table.add_row("Run directory", str(result.run_dir))
    table.add_row("Valid molecules", str(result.valid_count))
    table.add_row("Invalid molecules", str(result.invalid_count))
    table.add_row("Report", str(result.run_dir / "report.html"))
    console.print(table)


@app.command()
def init(target: Annotated[Path, TARGET_ARG] = Path(".")) -> None:
    """Create a minimal demo workspace."""
    target.mkdir(parents=True, exist_ok=True)
    molecules_dir = target / "examples" / "molecules"
    workflows_dir = target / "workflows"
    molecules_dir.mkdir(parents=True, exist_ok=True)
    workflows_dir.mkdir(parents=True, exist_ok=True)
    (molecules_dir / "demo_molecules.csv").write_text(
        DEMO_MOLECULES,
        encoding="utf-8",
    )
    (workflows_dir / "molecule_screen.yaml").write_text(
        DEMO_WORKFLOW,
        encoding="utf-8",
    )
    console.print(f"Initialized Open Drug Lab workspace at {target.resolve()}")
    console.print("Run: odl run workflows/molecule_screen.yaml")
