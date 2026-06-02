from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .workflow import WorkflowError, load_workflow, read_molecules, run_molecule_screen

app = typer.Typer(help="Open Drug Lab command line interface.")
console = Console()
CONFIG_ARG = typer.Argument(..., help="Path to a workflow YAML file.")
TARGET_ARG = typer.Argument(help="Directory to initialize.")
RUNS_DIR_OPT = typer.Option(None, help="Override the workflow output runs directory.")
FORCE_OPT = typer.Option(False, help="Overwrite existing demo files.")
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
def run(
    config: Annotated[Path, CONFIG_ARG],
    runs_dir: Annotated[Path | None, RUNS_DIR_OPT] = None,
) -> None:
    """Run a workflow and write artifacts to a run directory."""
    try:
        result = run_molecule_screen(config, runs_dir_override=runs_dir)
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
def init(
    target: Annotated[Path, TARGET_ARG] = Path("."),
    force: Annotated[bool, FORCE_OPT] = False,
) -> None:
    """Create a minimal demo workspace."""
    target.mkdir(parents=True, exist_ok=True)
    molecules_dir = target / "examples" / "molecules"
    workflows_dir = target / "workflows"
    molecules_dir.mkdir(parents=True, exist_ok=True)
    workflows_dir.mkdir(parents=True, exist_ok=True)
    _write_demo_file(
        molecules_dir / "demo_molecules.csv",
        DEMO_MOLECULES,
        force=force,
    )
    _write_demo_file(
        workflows_dir / "molecule_screen.yaml",
        DEMO_WORKFLOW,
        force=force,
    )
    console.print(f"Initialized Open Drug Lab workspace at {target.resolve()}")
    console.print("Run: odl run workflows/molecule_screen.yaml")


@app.command()
def validate(config: Annotated[Path, CONFIG_ARG]) -> None:
    """Validate workflow configuration and input CSV shape."""
    try:
        workflow = load_workflow(config)
        root = config.parent.parent if config.parent.name == "workflows" else Path.cwd()
        molecule_path = (
            workflow.inputs.molecules
            if workflow.inputs.molecules.is_absolute()
            else (root / workflow.inputs.molecules).resolve()
        )
        records = read_molecules(molecule_path)
    except WorkflowError as exc:
        console.print("[bold red]Validation failed:[/bold red]")
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc

    console.print("[bold green]Workflow config is valid.[/bold green]")
    console.print(f"Workflow: {workflow.workflow}")
    console.print(f"Molecule input: {molecule_path}")
    console.print(f"Rows: {len(records)}")


def _write_demo_file(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        console.print(f"Keeping existing file: {path}")
        return
    path.write_text(content, encoding="utf-8")
