from __future__ import annotations

import re
from pathlib import Path


def list_profile_sections_impl(data_dir: Path | None = None) -> str:
    """List available profile sections from local markdown files.

    Kept dependency-free so it can be unit-tested without network/LLM packages.
    """

    base = data_dir or (Path(__file__).resolve().parent / "data")
    if not base.exists():
        return "Aucune donnée trouvée (dossier data/ manquant)."

    heading_re = re.compile(r"^(#{1,3})\s+(.*)\s*$")
    lines: list[str] = ["Sections disponibles :"]

    for md_path in sorted(base.glob("*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception:
            continue

        headings: list[str] = []
        for raw in text.splitlines():
            m = heading_re.match(raw)
            if not m:
                continue
            level = len(m.group(1))
            title = m.group(2).strip()
            if not title:
                continue
            if level == 1:
                headings.append(title)
            elif level == 2:
                headings.append(f"- {title}")

        if headings:
            lines.append(f"\n{md_path.name}:")
            lines.extend(headings)

    return "\n".join(lines).strip()
