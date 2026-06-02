from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from .models import DescriptorRecord, FlagRecord, InvalidMoleculeRecord


def render_report(
    output_path: Path,
    *,
    title: str,
    descriptors: list[DescriptorRecord],
    flags: list[FlagRecord],
    invalid: list[InvalidMoleculeRecord],
    manifest: dict[str, Any],
) -> None:
    env = Environment(
        loader=PackageLoader("opendruglab", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    html = template.render(
        title=title,
        descriptors=descriptors,
        flags=flags,
        invalid=invalid,
        manifest=manifest,
    )
    output_path.write_text(html, encoding="utf-8")
