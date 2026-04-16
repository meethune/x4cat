"""Structural XML validation using SQLite-backed schema rules."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from x4_catalog._xml_utils import safe_parse

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from x4_catalog._types import ValidationReport


def validate_schema(
    mod_dir: Path,
    db_path: Path | str,
) -> ValidationReport:
    """Validate mod XML files against schema rules in the SQLite index.

    Checks:
    - Element names are valid in their parent context (actions, conditions, etc.)
    - Required attributes are present

    Returns ``{"errors": [...], "warnings": [...]}``.
    """
    import pathlib
    import sqlite3 as _sqlite3

    conn = _sqlite3.connect(db_path)

    # Load valid action/condition element names from schema_groups
    valid_actions = _load_group_elements(conn, "actions")
    valid_commonactions = _load_group_elements(conn, "commonactions")
    valid_conditions_event = _load_group_elements(conn, "commonconditions_event")
    valid_conditions_nonevent = _load_group_elements(conn, "commonconditions_nonevent")
    valid_conditions_spec_event = _load_group_elements(conn, "specificconditions_event")
    valid_conditions_spec_nonevent = _load_group_elements(conn, "specificconditions_nonevent")

    all_valid_actions = valid_actions | valid_commonactions
    all_valid_conditions = (
        valid_conditions_event
        | valid_conditions_nonevent
        | valid_conditions_spec_event
        | valid_conditions_spec_nonevent
    )

    # Load required attributes
    required_attrs = _load_required_attrs(conn)

    conn.close()

    errors: list[str] = []
    warnings: list[str] = []

    mod = pathlib.Path(mod_dir)
    for xml_path in sorted(mod.rglob("*.xml")):
        if not xml_path.is_file() or xml_path.is_symlink():
            continue

        # Skip translation files and non-script files
        rel = xml_path.relative_to(mod).as_posix()
        if not (rel.startswith("md/") or rel.startswith("aiscripts/")):
            continue

        try:
            root = safe_parse(xml_path)
        except (ET.ParseError, ValueError):
            continue

        if root.tag not in ("mdscript", "aiscript"):
            continue

        _validate_element_tree(
            root,
            rel,
            all_valid_actions,
            all_valid_conditions,
            required_attrs,
            errors,
            warnings,
        )

    return {"errors": errors, "warnings": warnings}


def _load_group_elements(conn: sqlite3.Connection, group_name: str) -> set[str]:
    """Load all element names belonging to a schema group."""
    rows = conn.execute(
        "SELECT element_name FROM schema_groups WHERE group_name = ?",
        (group_name,),
    ).fetchall()
    return {r[0] for r in rows}


def _load_required_attrs(
    conn: sqlite3.Connection,
) -> dict[str, list[str]]:
    """Load required attributes per element name."""
    rows = conn.execute(
        "SELECT element_name, attr_name FROM schema_attributes WHERE use = 'required'"
    ).fetchall()
    result: dict[str, list[str]] = {}
    for elem_name, attr_name in rows:
        result.setdefault(elem_name, []).append(attr_name)
    return result


def _validate_element_tree(
    root: ET.Element,
    file_path: str,
    valid_actions: set[str],
    valid_conditions: set[str],
    required_attrs: dict[str, list[str]],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Walk the element tree and validate elements in context."""
    # Known structural elements that are always valid
    structural = {
        "mdscript",
        "aiscript",
        "cues",
        "cue",
        "library",
        "conditions",
        "actions",
        "delay",
        "force",
        "patch",
        "patches",
        "params",
        "param",
        "interrupts",
        "handler",
        "init",
        "attention",
        "label",
        "return",
        "check_all",
        "check_any",
        "do_all",
        "do_for_each",
        "do_any",
        "do_if",
        "do_elseif",
        "do_else",
        "do_while",
    }

    # Build parent map once (O(n)) instead of per-element lookup (O(n²))
    parent_map: dict[int, ET.Element] = {
        id(child): parent for parent in root.iter() for child in parent
    }

    for elem in root.iter():
        tag = elem.tag

        # Skip structural elements
        if tag in structural:
            continue

        # Determine context from parent
        parent = parent_map.get(id(elem))
        if parent is None:
            continue
        parent_tag = parent.tag

        # Validate elements inside <actions>
        if parent_tag == "actions" or parent_tag in {
            "do_all",
            "do_for_each",
            "do_any",
            "do_if",
            "do_elseif",
            "do_else",
            "do_while",
        }:
            if valid_actions and tag not in valid_actions and tag not in structural:
                errors.append(f"{file_path}: unknown action <{tag}>")

        # Validate elements inside <conditions>
        elif (
            parent_tag in ("conditions", "check_all", "check_any")
            and valid_conditions
            and tag not in valid_conditions
            and tag not in structural
        ):
            errors.append(f"{file_path}: unknown condition <{tag}>")

        # Check required attributes
        if tag in required_attrs:
            for attr in required_attrs[tag]:
                if attr not in elem.attrib:
                    warnings.append(f"{file_path}: <{tag}> missing attribute '{attr}'")
