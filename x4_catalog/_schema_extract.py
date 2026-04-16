"""Extract XSD schema rules into SQLite for fast structural validation.

Parses X4 XSD files as plain XML using ElementTree and resolves
group references into flat lookup tables — no XSD compilation needed.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from x4_catalog._xml_utils import safe_fromstring

if TYPE_CHECKING:
    import sqlite3

if TYPE_CHECKING:
    from pathlib import Path

_XS = "{http://www.w3.org/2001/XMLSchema}"

_SCHEMA_TABLES_SQL = """\
CREATE TABLE IF NOT EXISTS schema_elements (
    element_name  TEXT NOT NULL,
    parent_context TEXT NOT NULL,
    type_ref      TEXT NOT NULL DEFAULT '',
    min_occurs    INTEGER NOT NULL DEFAULT 1,
    max_occurs    INTEGER,
    PRIMARY KEY (element_name, parent_context)
);

CREATE TABLE IF NOT EXISTS schema_attributes (
    element_name  TEXT NOT NULL,
    attr_name     TEXT NOT NULL,
    attr_type     TEXT NOT NULL DEFAULT 'xs:string',
    use           TEXT NOT NULL DEFAULT 'optional',
    default_val   TEXT,
    PRIMARY KEY (element_name, attr_name)
);

CREATE TABLE IF NOT EXISTS schema_enumerations (
    type_name TEXT NOT NULL,
    value     TEXT NOT NULL,
    PRIMARY KEY (type_name, value)
);

CREATE TABLE IF NOT EXISTS schema_groups (
    group_name TEXT NOT NULL,
    element_name TEXT NOT NULL,
    PRIMARY KEY (group_name, element_name)
);
"""


def _parse_max_occurs(val: str | None) -> int | None:
    if val is None or val == "1":
        return 1
    if val == "unbounded":
        return None
    return int(val)


class _XsdModel:
    """In-memory model of parsed XSD definitions."""

    def __init__(self) -> None:
        self.groups: dict[str, list[str]] = {}
        self.complex_types: dict[str, ET.Element] = {}
        self.attribute_groups: dict[str, list[tuple[str, str, str, str | None]]] = {}
        self.enumerations: dict[str, list[str]] = {}
        self.elements_by_type: dict[str, list[tuple[str, int, int | None]]] = {}

    def load_xsd(self, path: Path) -> None:
        """Load an XSD file, following xs:include."""
        root = ET.parse(path).getroot()
        self._process_root(root, path.parent)

    def _process_root(self, root: ET.Element, base_dir: Path) -> None:
        # Follow includes
        for inc in root.findall(f"{_XS}include"):
            loc = inc.get("schemaLocation", "")
            if loc:
                inc_path = base_dir / loc
                if inc_path.exists():
                    inc_root = ET.parse(inc_path).getroot()
                    self._process_root(inc_root, inc_path.parent)

        # Extract groups (merge if same name exists from another XSD)
        for g in root.findall(f"{_XS}group"):
            name = g.get("name")
            if not name:
                continue
            elements = self._extract_choice_elements(g)
            group_refs = [f"@group:{r}" for r in self._extract_group_refs(g)]
            existing = self.groups.get(name, [])
            self.groups[name] = existing + elements + group_refs

        # Extract complex types
        for ct in root.findall(f"{_XS}complexType"):
            name = ct.get("name")
            if name:
                self.complex_types[name] = ct

        # Extract attribute groups
        for ag in root.findall(f"{_XS}attributeGroup"):
            name = ag.get("name")
            if not name:
                continue
            attrs: list[tuple[str, str, str, str | None]] = []
            for a in ag.findall(f"{_XS}attribute"):
                a_name = a.get("name", "")
                a_type = a.get("type", "xs:string")
                a_use = a.get("use", "optional")
                a_default = a.get("default")
                if a_name:
                    attrs.append((a_name, a_type, a_use, a_default))
            existing_attrs = self.attribute_groups.get(name, [])
            self.attribute_groups[name] = existing_attrs + attrs

        # Extract enumerations from simple types
        for st in root.findall(f"{_XS}simpleType"):
            name = st.get("name", "")
            restriction = st.find(f"{_XS}restriction")
            if restriction is None:
                continue
            enums = [
                e.get("value", "")
                for e in restriction.findall(f"{_XS}enumeration")
                if e.get("value")
            ]
            if enums:
                self.enumerations[name] = enums

    def _extract_choice_elements(self, parent: ET.Element) -> list[str]:
        """Extract direct element names from choice/sequence groups."""
        elements: list[str] = []
        for elem in parent.iter(f"{_XS}element"):
            name = elem.get("name") or elem.get("ref")
            if name:
                elements.append(name)
        return elements

    def _extract_group_refs(self, parent: ET.Element) -> list[str]:
        """Extract group ref names from a group definition."""
        refs: list[str] = []
        for g in parent.iter(f"{_XS}group"):
            ref = g.get("ref")
            if ref:
                refs.append(ref)
        return refs

    def resolve_group(self, group_name: str, visited: set[str] | None = None) -> list[str]:
        """Recursively resolve a group to its flat list of element names."""
        if visited is None:
            visited = set()
        if group_name in visited:
            return []
        visited.add(group_name)

        raw = self.groups.get(group_name, [])
        resolved: list[str] = []
        for item in raw:
            if item.startswith("@group:"):
                ref = item[7:]
                resolved.extend(self.resolve_group(ref, visited))
            else:
                resolved.append(item)
        return resolved

    def get_complex_type_children(self, type_name: str) -> list[tuple[str, str]]:
        """Get child elements of a complex type as (name, type_ref) pairs."""
        ct = self.complex_types.get(type_name)
        if ct is None:
            return []
        children: list[tuple[str, str]] = []
        for elem in ct.iter(f"{_XS}element"):
            name = elem.get("name") or elem.get("ref", "")
            type_ref = elem.get("type", "")
            if name:
                children.append((name, type_ref))
        # Also resolve group refs within the complex type
        for g in ct.iter(f"{_XS}group"):
            ref = g.get("ref")
            if ref:
                for elem_name in self.resolve_group(ref):
                    children.append((elem_name, ""))
        return children

    def get_complex_type_attrs(self, type_name: str) -> list[tuple[str, str, str, str | None]]:
        """Get attributes of a complex type as (name, type, use, default)."""
        ct = self.complex_types.get(type_name)
        if ct is None:
            return []
        attrs: list[tuple[str, str, str, str | None]] = []
        for a in ct.iter(f"{_XS}attribute"):
            name = a.get("name", "")
            if name:
                attrs.append(
                    (name, a.get("type", "xs:string"), a.get("use", "optional"), a.get("default"))
                )
        for ag_ref in ct.iter(f"{_XS}attributeGroup"):
            ref = ag_ref.get("ref")
            if ref and ref in self.attribute_groups:
                attrs.extend(self.attribute_groups[ref])
        return attrs


def extract_schema_to_db(
    schema_dir: Path,
    conn: sqlite3.Connection,
) -> dict[str, int]:
    """Extract XSD rules from *schema_dir* into the SQLite connection.

    Expects the standard X4 schema layout under *schema_dir*:
    ``libraries/md.xsd``, ``libraries/aiscripts.xsd``, ``libraries/diff.xsd``.

    Returns counts of extracted items.
    """
    conn.executescript(_SCHEMA_TABLES_SQL)

    model = _XsdModel()

    # Load schema files (each includes common.xsd via xs:include)
    for xsd_name in ["libraries/md.xsd", "libraries/aiscripts.xsd", "libraries/diff.xsd"]:
        xsd_path = schema_dir / xsd_name
        if xsd_path.exists():
            model.load_xsd(xsd_path)

    # Write resolved groups
    group_count = 0
    for group_name in model.groups:
        resolved = model.resolve_group(group_name)
        for elem_name in resolved:
            conn.execute(
                "INSERT OR IGNORE INTO schema_groups (group_name, element_name) VALUES (?, ?)",
                (group_name, elem_name),
            )
            group_count += 1

    # Write element-parent relationships from complex types
    element_count = 0
    for type_name, _ct in model.complex_types.items():
        children = model.get_complex_type_children(type_name)
        for child_name, type_ref in children:
            conn.execute(
                "INSERT OR IGNORE INTO schema_elements "
                "(element_name, parent_context, type_ref) VALUES (?, ?, ?)",
                (child_name, type_name, type_ref),
            )
            element_count += 1

    # Write attributes
    attr_count = 0
    for type_name in model.complex_types:
        attrs = model.get_complex_type_attrs(type_name)
        # Find element names that use this type
        elem_names: list[str] = []
        for g_elements in model.groups.values():
            for raw in g_elements:
                if not raw.startswith("@group:"):
                    elem_names.append(raw)
        # Also check direct element definitions in complex types
        for _other_type, other_ct in model.complex_types.items():
            for elem in other_ct.iter(f"{_XS}element"):
                if elem.get("type") == type_name:
                    e_name = elem.get("name", "")
                    if e_name:
                        for a_name, a_type, a_use, a_default in attrs:
                            conn.execute(
                                "INSERT OR IGNORE INTO schema_attributes "
                                "(element_name, attr_name, attr_type, use, default_val) "
                                "VALUES (?, ?, ?, ?, ?)",
                                (e_name, a_name, a_type, a_use, a_default),
                            )
                            attr_count += 1

    # Write attributes for top-level types directly (cue, library, etc.)
    for type_name in model.complex_types:
        attrs = model.get_complex_type_attrs(type_name)
        for a_name, a_type, a_use, a_default in attrs:
            conn.execute(
                "INSERT OR IGNORE INTO schema_attributes "
                "(element_name, attr_name, attr_type, use, default_val) "
                "VALUES (?, ?, ?, ?, ?)",
                (type_name, a_name, a_type, a_use, a_default),
            )
            attr_count += 1

    # Write enumerations
    enum_count = 0
    for type_name, values in model.enumerations.items():
        for val in values:
            conn.execute(
                "INSERT OR IGNORE INTO schema_enumerations (type_name, value) VALUES (?, ?)",
                (type_name, val),
            )
            enum_count += 1

    return {
        "groups": group_count,
        "elements": element_count,
        "attributes": attr_count,
        "enumerations": enum_count,
    }


def extract_scriptproperties_to_db(
    scriptprops_data: bytes,
    conn: sqlite3.Connection,
) -> dict[str, int]:
    """Parse scriptproperties.xml and store in SQLite tables."""
    conn.executescript("""\
        CREATE TABLE IF NOT EXISTS script_datatypes (
            name       TEXT PRIMARY KEY,
            base_type  TEXT,
            suffix     TEXT,
            is_pseudo  INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS script_keywords (
            name        TEXT PRIMARY KEY,
            description TEXT NOT NULL DEFAULT '',
            type        TEXT,
            script      TEXT NOT NULL DEFAULT 'any'
        );
        CREATE TABLE IF NOT EXISTS script_properties (
            owner_name  TEXT NOT NULL,
            owner_kind  TEXT NOT NULL,
            prop_name   TEXT NOT NULL,
            result_desc TEXT NOT NULL DEFAULT '',
            result_type TEXT,
            PRIMARY KEY (owner_name, owner_kind, prop_name)
        );
    """)

    root = safe_fromstring(scriptprops_data)

    dt_count = 0
    for dt in root.findall("datatype"):
        name = dt.get("name", "")
        if not name:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO script_datatypes (name, base_type, suffix, is_pseudo) "
            "VALUES (?, ?, ?, ?)",
            (
                name,
                dt.get("type"),
                dt.get("suffix"),
                1 if dt.get("pseudo") == "true" else 0,
            ),
        )
        dt_count += 1
        for prop in dt.findall("property"):
            conn.execute(
                "INSERT OR IGNORE INTO script_properties VALUES (?, ?, ?, ?, ?)",
                (
                    name,
                    "datatype",
                    prop.get("name", ""),
                    prop.get("result", ""),
                    prop.get("type"),
                ),
            )

    kw_count = 0
    for kw in root.findall("keyword"):
        name = kw.get("name", "")
        if not name:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO script_keywords (name, description, type, script) "
            "VALUES (?, ?, ?, ?)",
            (
                name,
                kw.get("description", ""),
                kw.get("type"),
                kw.get("script", "any"),
            ),
        )
        kw_count += 1
        for prop in kw.findall("property"):
            conn.execute(
                "INSERT OR IGNORE INTO script_properties VALUES (?, ?, ?, ?, ?)",
                (
                    name,
                    "keyword",
                    prop.get("name", ""),
                    prop.get("result", ""),
                    prop.get("type"),
                ),
            )

    prop_count = conn.execute("SELECT COUNT(*) FROM script_properties").fetchone()[0]

    return {
        "datatypes": dt_count,
        "keywords": kw_count,
        "properties": prop_count,
    }
