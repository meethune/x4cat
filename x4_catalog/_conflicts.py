"""Detect conflicts between multiple mods' XML diff patches."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from x4_catalog._types import ConflictEntry, ConflictReport


def _scan_diff_ops(
    mod_dir: Path,
) -> dict[str, list[tuple[str, str]]]:
    """Scan a mod directory for diff patch operations.

    Returns ``{virtual_path: [(op_tag, sel), ...]}``.
    """
    import pathlib

    result: dict[str, list[tuple[str, str]]] = {}
    mod = pathlib.Path(mod_dir)

    for xml_path in sorted(mod.rglob("*.xml")):
        if not xml_path.is_file() or xml_path.is_symlink():
            continue
        try:
            root = ET.parse(xml_path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "diff":
            continue

        vpath = xml_path.relative_to(mod).as_posix()
        ops: list[tuple[str, str]] = []
        for op in root:
            if op.tag in ("add", "replace", "remove"):
                sel = op.get("sel", "")
                if sel:
                    ops.append((op.tag, sel))
        if ops:
            result[vpath] = ops

    return result


def _classify_overlap(
    ops_by_mod: dict[str, list[tuple[str, str]]],
    sel: str,
) -> str:
    """Classify an overlap as SAFE, CONFLICT, or INFO.

    ``ops_by_mod`` maps mod name to list of ``(tag, sel)`` for this specific sel.
    """
    tags: set[str] = set()
    for mod_ops in ops_by_mod.values():
        for tag, s in mod_ops:
            if s == sel:
                tags.add(tag)

    if tags == {"add"}:
        return "SAFE"
    replace_count = sum(
        1
        for mod_ops in ops_by_mod.values()
        if any(t == "replace" and s == sel for t, s in mod_ops)
    )
    if "replace" in tags and replace_count > 1:
        return "CONFLICT"
    if "remove" in tags and tags & {"replace", "add"}:
        return "CONFLICT"
    return "INFO"


def check_conflicts(
    mod_dirs: list[Path],
) -> ConflictReport:
    """Check for conflicts between multiple mods' diff patches.

    Returns a dict with:
    - ``conflicts``: list of conflict dicts (CONFLICT severity)
    - ``safe``: list of safe overlap dicts (SAFE severity)
    - ``info``: list of informational overlap dicts (INFO severity)
    - ``files_checked``: number of files with overlapping operations
    """
    import pathlib

    # Collect operations per mod
    all_ops: dict[str, dict[str, list[tuple[str, str]]]] = {}
    for mod_dir in mod_dirs:
        mod = pathlib.Path(mod_dir)
        mod_name = mod.name
        all_ops[mod_name] = _scan_diff_ops(mod)

    # Find files targeted by multiple mods
    file_to_mods: dict[str, set[str]] = {}
    for mod_name, file_ops in all_ops.items():
        for vpath in file_ops:
            file_to_mods.setdefault(vpath, set()).add(mod_name)

    shared_files = {f: mods for f, mods in file_to_mods.items() if len(mods) > 1}

    conflicts: list[ConflictEntry] = []
    safe: list[ConflictEntry] = []
    info: list[ConflictEntry] = []

    for vpath, mod_names in sorted(shared_files.items()):
        # Collect all sels for this file across mods
        sel_to_mods: dict[str, dict[str, list[tuple[str, str]]]] = {}
        for mod_name in mod_names:
            for tag, sel in all_ops[mod_name].get(vpath, []):
                sel_mods = sel_to_mods.setdefault(sel, {})
                sel_mods.setdefault(mod_name, []).append((tag, sel))

        # Pass 1: exact sel matches across mods
        for sel, ops_by_mod in sel_to_mods.items():
            if len(ops_by_mod) <= 1:
                continue

            severity = _classify_overlap(ops_by_mod, sel)
            entry: ConflictEntry = {
                "file": vpath,
                "sel": sel,
                "mods": sorted(ops_by_mod.keys()),
                "operations": {
                    mod: [t for t, s in mod_ops if s == sel] for mod, mod_ops in ops_by_mod.items()
                },
            }

            if severity == "CONFLICT":
                conflicts.append(entry)
            elif severity == "SAFE":
                safe.append(entry)
            else:
                info.append(entry)

        # Pass 2: cross-sel conflicts (remove on parent vs modify on child)
        # Collect all (mod, tag, sel) for this file
        all_file_ops: list[tuple[str, str, str]] = []
        for mod_name in mod_names:
            for tag, sel in all_ops[mod_name].get(vpath, []):
                all_file_ops.append((mod_name, tag, sel))

        removes = [(m, s) for m, t, s in all_file_ops if t == "remove"]
        non_removes = [(m, t, s) for m, t, s in all_file_ops if t != "remove"]

        for rm_mod, rm_sel in removes:
            for other_mod, other_tag, other_sel in non_removes:
                if rm_mod == other_mod:
                    continue
                # Check if the remove sel is a prefix of the other sel
                if other_sel.startswith(rm_sel) and other_sel != rm_sel:
                    cross_entry: ConflictEntry = {
                        "file": vpath,
                        "sel": f"{rm_sel} (removes parent of {other_sel})",
                        "mods": sorted({rm_mod, other_mod}),
                        "operations": {
                            rm_mod: ["remove"],
                            other_mod: [other_tag],
                        },
                    }
                    conflicts.append(cross_entry)

    return {
        "conflicts": conflicts,
        "safe": safe,
        "info": info,
        "files_checked": len(shared_files),
    }
