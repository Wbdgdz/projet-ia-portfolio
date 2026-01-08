from __future__ import annotations

from pathlib import Path

from chunk_data import build_chunks_for_file, chunk_markdown, iter_markdown_files, normalize_ws


def test_normalize_ws_trims_and_newline():
    assert normalize_ws("\n\n  a  \n\n") == "a\n"


def test_chunk_markdown_excludes_heading_lines_and_splits_on_h2():
    md = """# Title

## Section A
Line 1

## Section B
Line 2
"""
    chunks = chunk_markdown(md)

    assert len(chunks) == 2
    (path_a, text_a), (path_b, text_b) = chunks

    assert path_a == ["Title", "Section A"]
    assert path_b == ["Title", "Section B"]

    assert "##" not in text_a
    assert "# Title" not in text_a
    assert "Line 1" in text_a

    assert "##" not in text_b
    assert "Line 2" in text_b


def test_build_chunks_for_file(tmp_path: Path):
    md_path = tmp_path / "demo.md"
    md_path.write_text("# T\n\n## A\nhello\n\n## B\nworld\n", encoding="utf-8")

    chunks = build_chunks_for_file(md_path)
    assert [c.id for c in chunks] == ["demo-001", "demo-002"]
    assert chunks[0].source_file == "demo.md"
    assert chunks[0].heading_path == ["T", "A"]
    assert "hello" in chunks[0].content


def test_iter_markdown_files_excludes_readme(tmp_path: Path):
    (tmp_path / "README.md").write_text("# ignore", encoding="utf-8")
    (tmp_path / "01_a.md").write_text("# a", encoding="utf-8")
    (tmp_path / "02_b.MD").write_text("# b", encoding="utf-8")

    files = list(iter_markdown_files(tmp_path))
    assert [p.name for p in files] == ["01_a.md", "02_b.MD"]
