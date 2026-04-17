"""Search X4 game assets by ID, name, group, or tags using the SQLite index."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcards for literal matching."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search_assets(
    term: str,
    db_path: Path | str,
    *,
    type_filter: str | None = None,
) -> list[dict[str, str]]:
    """Search across wares, macros, components, datatypes, and keywords.

    Returns a list of dicts with keys: ``id``, ``type``, ``path``, ``detail``.
    Case-insensitive substring matching on IDs, names, groups, and tags.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        results: list[dict[str, str]] = []
        escaped = _escape_like(term)
        pattern = f"%{escaped}%"

        if type_filter is None or type_filter == "ware":
            _search_wares(conn, pattern, results)
        if type_filter is None or type_filter == "macro":
            _search_macros(conn, pattern, results)
        if type_filter is None or type_filter == "component":
            _search_components(conn, pattern, results)
        if type_filter is None or type_filter == "datatype":
            _search_datatypes(conn, pattern, results)
        if type_filter is None or type_filter == "keyword":
            _search_keywords(conn, pattern, results)

        return results
    finally:
        conn.close()


def _search_wares(conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]) -> None:
    rows = conn.execute(
        "SELECT ware_id, name_ref, name_resolved, ware_group, tags, price_avg "
        "FROM wares "
        "WHERE ware_id LIKE ? ESCAPE '\\' COLLATE NOCASE "
        "OR name_ref LIKE ? ESCAPE '\\' COLLATE NOCASE "
        "OR name_resolved LIKE ? ESCAPE '\\' COLLATE NOCASE "
        "OR ware_group LIKE ? ESCAPE '\\' COLLATE NOCASE "
        "OR tags LIKE ? ESCAPE '\\' COLLATE NOCASE",
        (pattern, pattern, pattern, pattern, pattern),
    ).fetchall()
    for r in rows:
        detail = r["ware_group"] or ""
        if r["name_resolved"]:
            detail = f"{r['name_resolved']} [{detail}]" if detail else r["name_resolved"]
        if r["price_avg"]:
            detail += f" avg:{r['price_avg']}"
        results.append(
            {
                "id": r["ware_id"],
                "type": "ware",
                "path": "",
                "detail": detail.strip(),
            }
        )


def _search_macros(conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]) -> None:
    rows = conn.execute(
        "SELECT name, value FROM macros WHERE name LIKE ? ESCAPE '\\' COLLATE NOCASE",
        (pattern,),
    ).fetchall()
    for r in rows:
        results.append(
            {
                "id": r["name"],
                "type": "macro",
                "path": r["value"] + ".xml",
                "detail": "",
            }
        )


def _search_components(
    conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]
) -> None:
    rows = conn.execute(
        "SELECT name, value FROM components WHERE name LIKE ? ESCAPE '\\' COLLATE NOCASE",
        (pattern,),
    ).fetchall()
    for r in rows:
        results.append(
            {
                "id": r["name"],
                "type": "component",
                "path": r["value"] + ".xml",
                "detail": "",
            }
        )


def _search_datatypes(
    conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]
) -> None:
    try:
        rows = conn.execute(
            "SELECT name, base_type FROM script_datatypes "
            "WHERE name LIKE ? ESCAPE '\\' COLLATE NOCASE",
            (pattern,),
        ).fetchall()
    except sqlite3.OperationalError:
        return
    for r in rows:
        detail = f"base: {r['base_type']}" if r["base_type"] else ""
        results.append(
            {
                "id": r["name"],
                "type": "datatype",
                "path": "",
                "detail": detail,
            }
        )


def _search_keywords(
    conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]
) -> None:
    try:
        rows = conn.execute(
            "SELECT name, description, script FROM script_keywords "
            "WHERE name LIKE ? ESCAPE '\\' COLLATE NOCASE "
            "OR description LIKE ? ESCAPE '\\' COLLATE NOCASE",
            (pattern, pattern),
        ).fetchall()
    except sqlite3.OperationalError:
        return
    for r in rows:
        detail = r["description"] or ""
        if r["script"]:
            detail += f" [{r['script']}]"
        results.append(
            {
                "id": r["name"],
                "type": "keyword",
                "path": "",
                "detail": detail.strip(),
            }
        )


def format_search_output(results: list[dict[str, str]]) -> str:
    """Format search results as a table."""
    if not results:
        return "0 results"

    lines: list[str] = []
    for r in sorted(results, key=lambda x: (x["type"], x["id"])):
        parts = [f"  {r['type']:10s}  {r['id']}"]
        if r["path"]:
            parts.append(f"  ({r['path']})")
        if r["detail"]:
            parts.append(f"  \u2014 {r['detail']}")
        lines.append("".join(parts))

    lines.append(f"\n{len(results)} result(s)")
    return "\n".join(lines)
