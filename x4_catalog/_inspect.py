"""Inspect X4 game assets by ID using the SQLite index."""

from __future__ import annotations

import sqlite3
from typing import Any


def inspect_asset(asset_id: str, db_path: Any) -> dict[str, Any] | None:
    """Look up an asset by ware ID, macro name, or component name.

    Returns a dict with all known information, or None if not found.
    Tries ware ID first, then macro name, then component name.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        result = _try_ware(conn, asset_id)
        if result is not None:
            return result
        result = _try_macro(conn, asset_id)
        if result is not None:
            return result
        return _try_component(conn, asset_id)
    finally:
        conn.close()


def _try_ware(conn: sqlite3.Connection, ware_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM wares WHERE ware_id = ?", (ware_id,)).fetchone()
    if row is None:
        return None

    result: dict[str, Any] = dict(row)

    # Owners
    owners = conn.execute(
        "SELECT faction FROM ware_owners WHERE ware_id = ?", (ware_id,)
    ).fetchall()
    result["owners"] = [r[0] for r in owners]

    # Try to find a linked macro (ware_id + _macro convention)
    macro_name = ware_id + "_macro"
    macro_row = conn.execute(
        "SELECT name, value FROM macros WHERE name = ?", (macro_name,)
    ).fetchone()
    if macro_row is not None:
        result["macro_name"] = macro_row["name"]
        result["macro_path"] = macro_row["value"]
        _attach_macro_properties(conn, macro_row["name"], result)

    return result


def _try_macro(conn: sqlite3.Connection, macro_name: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT name, value FROM macros WHERE name = ?", (macro_name,)).fetchone()
    if row is None:
        return None

    result: dict[str, Any] = {
        "macro_name": row["name"],
        "macro_path": row["value"],
    }

    _attach_macro_properties(conn, macro_name, result)

    # Try to find linked ware (strip _macro suffix)
    ware_id_candidate = macro_name.removesuffix("_macro")
    ware_row = conn.execute(
        "SELECT * FROM wares WHERE ware_id = ?", (ware_id_candidate,)
    ).fetchone()
    if ware_row is not None:
        result["ware_id"] = ware_row["ware_id"]
        result["price_min"] = ware_row["price_min"]
        result["price_avg"] = ware_row["price_avg"]
        result["price_max"] = ware_row["price_max"]
        owners = conn.execute(
            "SELECT faction FROM ware_owners WHERE ware_id = ?",
            (ware_id_candidate,),
        ).fetchall()
        result["owners"] = [r[0] for r in owners]

    return result


def _try_component(conn: sqlite3.Connection, comp_name: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT name, value FROM components WHERE name = ?", (comp_name,)
    ).fetchone()
    if row is None:
        return None
    return {
        "component_name": row["name"],
        "component_path": row["value"],
    }


def _attach_macro_properties(
    conn: sqlite3.Connection, macro_name: str, result: dict[str, Any]
) -> None:
    """Attach macro properties and component ref to the result dict."""
    props_rows = conn.execute(
        "SELECT property_key, property_val FROM macro_properties WHERE macro_name = ?",
        (macro_name,),
    ).fetchall()
    props: dict[str, str] = {}
    for r in props_rows:
        key, val = r[0], r[1]
        if key == "component_ref":
            result["component_ref"] = val
            # Look up component path
            comp_row = conn.execute(
                "SELECT value FROM components WHERE name = ?", (val,)
            ).fetchone()
            if comp_row is not None:
                result["component_path"] = comp_row[0]
        elif key == "class":
            result["macro_class"] = val
        else:
            props[key] = val
    if props:
        result["properties"] = props


def format_inspect_output(result: dict[str, Any]) -> str:
    """Format an inspect result as human-readable text."""
    lines: list[str] = []

    # Header
    if "macro_name" in result:
        macro_class = result.get("macro_class", "")
        label = f" ({macro_class})" if macro_class else ""
        lines.append(f"{result['macro_name']}{label}")
    elif "ware_id" in result:
        group = result.get("ware_group", "")
        label = f" ({group})" if group else ""
        lines.append(f"{result['ware_id']}{label}")
    elif "component_name" in result:
        lines.append(result["component_name"])

    # File paths
    if "macro_path" in result:
        lines.append(f"  Macro: {result['macro_path']}.xml")
    if "component_path" in result:
        lines.append(f"  Component: {result['component_path']}.xml")
    if "component_ref" in result and "component_path" not in result:
        lines.append(f"  Component ref: {result['component_ref']}")

    # Ware info
    if "ware_id" in result and "price_avg" in result:
        lines.append(
            f"  Price: {result['price_min']} / {result['price_avg']} / {result['price_max']}"
            "  (min / avg / max)"
        )
    if result.get("owners"):
        lines.append(f"  Owners: {', '.join(result['owners'])}")
    if result.get("name_ref"):
        lines.append(f"  Name ref: {result['name_ref']}")

    # Macro properties
    props = result.get("properties", {})
    if props:
        lines.append("  Properties:")
        for key in sorted(props):
            lines.append(f"    {key}: {props[key]}")

    return "\n".join(lines)
