"""Search X4 game assets by ID, group, or tags using the SQLite index."""

from __future__ import annotations

import sqlite3
from typing import Any


def search_assets(
    term: str,
    db_path: Any,
    *,
    type_filter: str | None = None,
) -> list[dict[str, str]]:
    """Search across wares, macros, and components by partial match.

    Returns a list of dicts with keys: ``id``, ``type``, ``path``, ``detail``.
    Case-insensitive substring matching on IDs, groups, and tags.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        results: list[dict[str, str]] = []
        pattern = f"%{term}%"

        if type_filter is None or type_filter == "ware":
            _search_wares(conn, pattern, results)
        if type_filter is None or type_filter == "macro":
            _search_macros(conn, pattern, results)
        if type_filter is None or type_filter == "component":
            _search_components(conn, pattern, results)

        return results
    finally:
        conn.close()


def _search_wares(conn: sqlite3.Connection, pattern: str, results: list[dict[str, str]]) -> None:
    rows = conn.execute(
        "SELECT ware_id, name_ref, ware_group, tags, price_avg FROM wares "
        "WHERE ware_id LIKE ? COLLATE NOCASE "
        "OR ware_group LIKE ? COLLATE NOCASE "
        "OR tags LIKE ? COLLATE NOCASE",
        (pattern, pattern, pattern),
    ).fetchall()
    for r in rows:
        detail = r["ware_group"] or ""
        if r["tags"]:
            detail = f"{detail} [{r['tags']}]" if detail else f"[{r['tags']}]"
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
        "SELECT name, value FROM macros WHERE name LIKE ? COLLATE NOCASE",
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
        "SELECT name, value FROM components WHERE name LIKE ? COLLATE NOCASE",
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
            parts.append(f"  — {r['detail']}")
        lines.append("".join(parts))

    lines.append(f"\n{len(results)} result(s)")
    return "\n".join(lines)
