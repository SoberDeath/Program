"""Regression checks for repository integrity and application imports."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_text_files_have_no_merge_conflict_markers() -> None:
    """Prevent an accidentally unresolved merge from entering the branch."""
    markers = ("<" * 7, "=" * 7, ">" * 7)
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        assert not any(line.startswith(markers) for line in lines), path
