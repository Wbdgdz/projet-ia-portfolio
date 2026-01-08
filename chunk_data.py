from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Chunk:
    id: str
    source_file: str
    heading_path: list[str]
    content: str


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")


def iter_markdown_files(data_dir: Path) -> Iterable[Path]:
    return sorted(p for p in data_dir.glob("*.md") if p.is_file() and p.name.lower() != "readme.md")


def normalize_ws(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines).strip() + "\n"


def chunk_markdown(md_text: str) -> list[tuple[list[str], str]]:
    """Return list of (heading_path, chunk_text).

    Strategy (simple and robust):
    - Track the current path of headings.
    - Create a chunk whenever we hit a '##' (level 2) heading.
    - If no '##' exists, fall back to whole document under '#'.
    """
    lines = md_text.splitlines(keepends=False)

    current_h1: str | None = None
    current_h2: str | None = None
    buffer: list[str] = []
    chunks: list[tuple[list[str], str]] = []

    def flush():
        nonlocal buffer
        if not buffer:
            return
        path: list[str] = []
        if current_h1:
            path.append(current_h1)
        if current_h2:
            path.append(current_h2)
        text = normalize_ws("\n".join(buffer))
        if text.strip():
            chunks.append((path, text))
        buffer = []

    has_h2 = False
    for l in lines:
        m = _HEADING_RE.match(l)
        if m and m.group(1) == "##":
            has_h2 = True
            break

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()

            if level == 1:
                current_h1 = title
                current_h2 = None
                # Never include heading lines in chunk content.
                # If the document has no ##, we will accumulate everything under this H1.
                continue

            if level == 2:
                flush()
                current_h2 = title
                continue

        buffer.append(line)

    flush()

    # If we found no chunks (empty file), return empty.
    return chunks


def build_chunks_for_file(md_path: Path) -> list[Chunk]:
    md_text = md_path.read_text(encoding="utf-8")
    pairs = chunk_markdown(md_text)

    chunks: list[Chunk] = []
    for idx, (heading_path, content) in enumerate(pairs, start=1):
        chunk_id = f"{md_path.stem}-{idx:03d}"
        chunks.append(
            Chunk(
                id=chunk_id,
                source_file=md_path.name,
                heading_path=heading_path,
                content=content,
            )
        )

    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description="Chunk Markdown files under ./data into JSONL.")
    parser.add_argument("--data-dir", default="data", help="Directory containing markdown files")
    parser.add_argument("--out", default="chunks.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    data_dir = (repo_root / args.data_dir).resolve()
    out_path = (repo_root / args.out).resolve()

    if not data_dir.exists() or not data_dir.is_dir():
        raise SystemExit(f"data dir not found: {data_dir}")

    all_chunks: list[Chunk] = []
    for md_file in iter_markdown_files(data_dir):
        all_chunks.extend(build_chunks_for_file(md_file))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(
                json.dumps(
                    {
                        "id": c.id,
                        "source_file": c.source_file,
                        "heading_path": c.heading_path,
                        "content": c.content,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Wrote {len(all_chunks)} chunks to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
