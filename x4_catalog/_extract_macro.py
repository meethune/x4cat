"""Extract a macro file by ID, resolving through the SQLite index."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from x4_catalog._core import build_vfs, read_payload
from x4_catalog._index import vfs_get_ci

if TYPE_CHECKING:
    from pathlib import Path


def extract_macro(
    macro_id: str,
    db_path: Path | str,
    game_dir: Path,
    output_dir: Path,
) -> Path | None:
    """Extract a macro file by ID to *output_dir*, preserving its virtual path.

    Returns the path to the extracted file, or ``None`` if the macro is not found.
    """
    import pathlib

    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT value FROM macros WHERE name = ?", (macro_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    vpath: str = row[0] + ".xml"
    vfs = build_vfs(game_dir)
    entry = vfs_get_ci(vfs, vpath)
    if entry is None:
        return None

    data = read_payload(entry)
    resolved_output = pathlib.Path(output_dir).resolve()
    dest = (resolved_output / vpath).resolve()
    if not dest.is_relative_to(resolved_output):
        raise ValueError(f"Path traversal detected: {vpath!r} escapes output directory")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest
