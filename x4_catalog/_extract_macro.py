"""Extract a macro file by ID, resolving through the SQLite index."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any

from x4_catalog._core import _read_payload, build_vfs
from x4_catalog._index import _vfs_get_ci

if TYPE_CHECKING:
    from pathlib import Path


def extract_macro(
    macro_id: str,
    db_path: Any,
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
    entry = _vfs_get_ci(vfs, vpath)
    if entry is None:
        return None

    data = _read_payload(entry)
    dest = pathlib.Path(output_dir) / vpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest
