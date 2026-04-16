"""Validate and scaffold X4 translation files."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_REF_PATTERN = re.compile(r"\{(\d+),(\d+)\}")


def _safe_int(val: str, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# Base game page IDs are below this threshold.
# Mods should use page IDs >= 90000 to avoid collisions.
_MOD_PAGE_THRESHOLD = 90000

# Known base game page ID range (v9.00: 1001–30622).
_BASE_GAME_MAX_PAGE = 31000


def _scan_refs(mod_dir: Path) -> set[tuple[int, int]]:
    """Scan all XML files in *mod_dir* for ``{pageId,entryId}`` references.

    Only collects references with page IDs >= _MOD_PAGE_THRESHOLD
    (base game references are not expected to have local translations).
    """
    import pathlib

    refs: set[tuple[int, int]] = set()
    for xml_path in pathlib.Path(mod_dir).rglob("*.xml"):
        if not xml_path.is_file() or xml_path.is_symlink():
            continue
        # Skip translation files themselves
        if "/t/" in str(xml_path) or "\\t\\" in str(xml_path):
            continue
        try:
            text = xml_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in _REF_PATTERN.finditer(text):
            page_id = int(match.group(1))
            entry_id = int(match.group(2))
            if page_id >= _MOD_PAGE_THRESHOLD:
                refs.add((page_id, entry_id))
    return refs


def _parse_translations(
    mod_dir: Path,
) -> dict[int, dict[int, dict[int, str]]]:
    """Parse all ``t/*.xml`` files in *mod_dir*.

    Returns ``{lang_code: {page_id: {entry_id: text}}}``.
    """
    import pathlib

    result: dict[int, dict[int, dict[int, str]]] = {}
    t_dir = pathlib.Path(mod_dir) / "t"
    if not t_dir.is_dir():
        return result

    for t_file in sorted(t_dir.glob("*.xml")):
        if not t_file.is_file():
            continue
        try:
            root = ET.parse(t_file).getroot()
        except ET.ParseError:
            continue
        if root.tag != "language":
            continue
        lang_code = _safe_int(root.get("id", "0"))
        if lang_code == 0:
            continue
        lang_data = result.setdefault(lang_code, {})
        for page in root.findall("page"):
            page_id = _safe_int(page.get("id", "0"))
            if page_id == 0:
                continue
            page_data = lang_data.setdefault(page_id, {})
            for t in page.findall("t"):
                entry_id = _safe_int(t.get("id", "0"))
                if entry_id:
                    page_data[entry_id] = t.text or ""
    return result


def _load_base_game_pages(db_path: Any) -> set[int]:
    """Load base game translation page IDs from the index DB."""
    import sqlite3

    if db_path is None:
        return set()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT page_id FROM translation_pages").fetchall()
        return {r[0] for r in rows}
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        return set()
    finally:
        conn.close()


def _check_page_collisions(
    translations: dict[int, dict[int, dict[int, str]]],
    base_game_pages: set[int] | None = None,
) -> list[str]:
    """Warn if any mod translation page ID collides with base game."""
    warnings: list[str] = []
    seen_pages: set[int] = set()
    for lang_data in translations.values():
        seen_pages.update(lang_data.keys())

    for page_id in sorted(seen_pages):
        if base_game_pages and page_id in base_game_pages:
            warnings.append(
                f"Page ID {page_id} collides with base game (exact match found in game index)"
            )
        elif page_id < _MOD_PAGE_THRESHOLD:
            warnings.append(
                f"Page ID {page_id} may collide with base game "
                f"(base game uses 1001–{_BASE_GAME_MAX_PAGE}, "
                f"mods should use {_MOD_PAGE_THRESHOLD}+)"
            )
    return warnings


def validate_translations(
    mod_dir: Path,
    db_path: Any = None,
) -> dict[str, Any]:
    """Validate translation files against text references in mod XML.

    If *db_path* is provided, uses the SQLite index for accurate base game
    page ID collision detection.

    Returns a dict with ``errors`` (list[str]) and ``warnings`` (list[str]).
    """
    refs = _scan_refs(mod_dir)
    translations = _parse_translations(mod_dir)
    base_game_pages = _load_base_game_pages(db_path) if db_path else None

    errors: list[str] = []
    warnings: list[str] = []

    # Use English (44) as the primary translation source
    primary_lang = 44
    primary = translations.get(primary_lang, {})

    # Check for missing translations
    defined: set[tuple[int, int]] = set()
    for page_id, entries in primary.items():
        for entry_id in entries:
            defined.add((page_id, entry_id))

    # Also collect defined entries from all languages
    all_defined: set[tuple[int, int]] = set()
    for lang_data in translations.values():
        for page_id, entries in lang_data.items():
            for entry_id in entries:
                all_defined.add((page_id, entry_id))

    for page_id, entry_id in sorted(refs - all_defined):
        errors.append(
            f"MISSING: {{{page_id},{entry_id}}} referenced in mod XML "
            f"but not defined in any translation file"
        )

    # Check for orphaned translations (defined but not referenced)
    mod_defined = {
        (p, e) for p, entries in primary.items() for e in entries if p >= _MOD_PAGE_THRESHOLD
    }
    for page_id, entry_id in sorted(mod_defined - refs):
        warnings.append(
            f"ORPHAN: {{{page_id},{entry_id}}} defined in translation "
            f"but not referenced in mod XML"
        )

    # Page ID collision warnings
    warnings.extend(_check_page_collisions(translations, base_game_pages))

    # Inconsistent entries across languages
    if len(translations) > 1:
        primary_entries: dict[int, set[int]] = {}
        for page_id, entries in primary.items():
            primary_entries[page_id] = set(entries.keys())

        for lang_code, lang_data in sorted(translations.items()):
            if lang_code == primary_lang:
                continue
            for page_id, primary_ids in primary_entries.items():
                lang_ids = set(lang_data.get(page_id, {}).keys())
                missing = primary_ids - lang_ids
                if missing:
                    warnings.append(
                        f"INCOMPLETE: language {lang_code}, page {page_id} "
                        f"missing entries: {sorted(missing)}"
                    )

    return {"errors": errors, "warnings": warnings}


def scaffold_translation(
    source_path: Path,
    output_path: Path,
    *,
    lang_code: int,
) -> None:
    """Generate a translation stub from an existing translation file.

    Copies the page/entry structure with ``[TRANSLATE: original text]`` markers.
    """
    import pathlib

    source = ET.parse(source_path).getroot()
    new_root = ET.Element("language", id=str(lang_code))

    for page in source.findall("page"):
        new_page = ET.SubElement(new_root, "page")
        for attr, val in page.attrib.items():
            new_page.set(attr, val)

        for t in page.findall("t"):
            new_t = ET.SubElement(new_page, "t", id=t.get("id", ""))
            original = t.text or ""
            new_t.text = f"[TRANSLATE: {original}]"

    out = pathlib.Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    from x4_catalog._scaffold import _indent_xml

    _indent_xml(new_root)
    data = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        + ET.tostring(new_root, encoding="unicode").encode()
    )
    out.write_bytes(data)
