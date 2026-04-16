"""Scaffold X4 mod content — wares, equipment, and ships."""

from __future__ import annotations

import sqlite3
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

from x4_catalog._core import _read_payload, build_vfs
from x4_catalog._index import _vfs_get_ci

if TYPE_CHECKING:
    from pathlib import Path

_DEFAULT_PAGE_ID = 90001


def _validate_id(value: str, label: str) -> None:
    """Reject IDs containing path separators or traversal sequences."""
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {label}: {value!r} (must not contain path separators or '..')")


def _indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Indent an element tree for pretty printing."""
    indent = "\n" + "  " * (level + 1)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent
        for i, child in enumerate(elem):
            _indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent if i < len(elem) - 1 else "\n" + "  " * level
    if not elem.tail or not elem.tail.strip():
        elem.tail = "\n" + "  " * level


def _write_xml(path: Any, root: ET.Element) -> None:
    """Write an XML element to a file with declaration and indentation."""
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    _indent_xml(root)
    data = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        + ET.tostring(root, encoding="unicode").encode()
    )
    p.write_bytes(data)


def _make_translation(
    path: Any,
    page_id: int,
    entries: dict[int, str],
    page_title: str = "",
) -> None:
    """Write a translation file with the given entries."""
    lang = ET.Element("language", id="44")
    page = ET.SubElement(lang, "page", id=str(page_id), title=page_title)
    for entry_id, text in sorted(entries.items()):
        t = ET.SubElement(page, "t", id=str(entry_id))
        t.text = text
    _write_xml(path, lang)


def _make_wares_diff(
    path: Any,
    ware_id: str,
    name_ref: str,
    desc_ref: str,
    *,
    group: str = "",
    transport: str = "container",
    volume: int = 1,
    tags: str = "container economy",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    component_ref: str = "",
) -> None:
    """Write a wares.xml diff patch that adds a new ware."""
    diff = ET.Element("diff")
    add = ET.SubElement(diff, "add", sel="/wares")

    ware = ET.SubElement(add, "ware")
    ware.set("id", ware_id)
    ware.set("name", name_ref)
    if desc_ref:
        ware.set("description", desc_ref)
    if group:
        ware.set("group", group)
    ware.set("transport", transport)
    ware.set("volume", str(volume))
    ware.set("tags", tags)
    ET.SubElement(
        ware,
        "price",
        min=str(price_min),
        average=str(price_avg),
        max=str(price_max),
    )
    if component_ref:
        ET.SubElement(ware, "component", ref=component_ref)
    ET.SubElement(ware, "icon", active="ware_default", video="ware_noicon_macro")

    _write_xml(path, diff)


# --- Tier 1: scaffold ware ---


def scaffold_ware(
    ware_id: str,
    name: str,
    output_dir: Path,
    *,
    description: str = "",
    group: str = "",
    transport: str = "container",
    volume: int = 1,
    tags: str = "container economy",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = _DEFAULT_PAGE_ID,
) -> list[str]:
    """Scaffold a simple trade ware (Tier 1 — no macro needed).

    Returns a list of generated file paths (relative to output_dir).
    """
    _validate_id(ware_id, "ware_id")

    if not description:
        description = f"A custom {name}"

    # Auto-derive price range if only avg provided
    if price_avg and not price_min:
        price_min = int(price_avg * 0.85)
    if price_avg and not price_max:
        price_max = int(price_avg * 1.15)

    name_ref = f"{{{page_id},1}}"
    desc_ref = f"{{{page_id},2}}"

    import pathlib

    out = pathlib.Path(output_dir)

    _make_wares_diff(
        out / "libraries" / "wares.xml",
        ware_id,
        name_ref,
        desc_ref,
        group=group,
        transport=transport,
        volume=volume,
        tags=tags,
        price_min=price_min,
        price_avg=price_avg,
        price_max=price_max,
    )

    _make_translation(
        out / "t" / "0001-l044.xml",
        page_id,
        {1: name, 2: description},
        page_title=ware_id,
    )

    return ["libraries/wares.xml", "t/0001-l044.xml"]


# --- Tier 2: scaffold equipment ---


def scaffold_equipment(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Any = None,
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = _DEFAULT_PAGE_ID,
) -> list[str]:
    """Scaffold an equipment item (Tier 2 — macro + index + ware + translation).

    Requires ``clone_from`` to specify an existing macro to clone.
    Returns a list of generated file paths (relative to output_dir).
    """
    _validate_id(macro_id, "macro_id")

    if not clone_from:
        raise ValueError("--clone-from is required for equipment scaffolding")

    if db_path is None:
        raise ValueError("Index DB path is required for equipment scaffolding")

    import pathlib

    out = pathlib.Path(output_dir)

    # Look up the source macro
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT value FROM macros WHERE name = ?", (clone_from,)).fetchone()
        if row is None:
            raise ValueError(f"Macro not found in index: {clone_from}")
        source_path = row[0]

        # Get game_dir from meta
        meta_row = conn.execute("SELECT value FROM meta WHERE key = 'game_dir'").fetchone()
    finally:
        conn.close()

    if meta_row is None:
        raise ValueError("Index does not contain game_dir metadata")

    game_dir = pathlib.Path(meta_row[0])

    # Read the source macro from the VFS
    vfs = build_vfs(game_dir)
    vpath = source_path + ".xml"
    entry = _vfs_get_ci(vfs, vpath)
    if entry is None:
        raise ValueError(f"Macro file not found in VFS: {vpath}")

    source_data = _read_payload(entry)
    source_root = ET.fromstring(source_data)
    source_macro = source_root.find("macro")
    if source_macro is None:
        raise ValueError(f"No <macro> element in {vpath}")

    # Clone and rename
    macro_class = source_macro.get("class", "object")
    component_ref = ""
    comp_elem = source_macro.find("component")
    if comp_elem is not None:
        component_ref = comp_elem.get("ref", "")

    # Build new macro XML
    new_root = ET.Element("macros")
    new_macro = ET.SubElement(new_root, "macro", name=macro_id)
    new_macro.set("class", macro_class)
    if component_ref:
        ET.SubElement(new_macro, "component", ref=component_ref)

    # Copy properties, update identification
    source_props = source_macro.find("properties")
    if source_props is not None:
        new_props = ET.SubElement(new_macro, "properties")
        for prop in source_props:
            new_prop = ET.SubElement(new_props, prop.tag, attrib=dict(prop.attrib))
            for sub in prop:
                ET.SubElement(new_prop, sub.tag, attrib=dict(sub.attrib))
        # Override identification name ref
        ident = new_props.find("identification")
        if ident is not None:
            ident.set("name", f"{{{page_id},1}}")
            ident.set("description", f"{{{page_id},2}}")

    # Determine macro file path (mirror source structure)
    macro_rel = source_path.replace("\\", "/")
    # Replace the source macro name with the new one
    macro_dir = "/".join(macro_rel.split("/")[:-1])
    new_macro_rel = f"{macro_dir}/{macro_id}"
    macro_file = f"{new_macro_rel}.xml"

    _write_xml(out / macro_file, new_root)

    # Index diff: register the new macro
    idx_diff = ET.Element("diff")
    idx_add = ET.SubElement(idx_diff, "add", sel="/index")
    ET.SubElement(
        idx_add,
        "entry",
        name=macro_id,
        value=new_macro_rel.replace("/", "\\"),
    )
    _write_xml(out / "index" / "macros.xml", idx_diff)

    # Ware ID: macro name without _macro suffix
    ware_id = macro_id.removesuffix("_macro")

    # Derive prices from source if not provided
    if not price_avg:
        conn2 = sqlite3.connect(db_path)
        source_ware_id = clone_from.removesuffix("_macro")
        ware_row = conn2.execute(
            "SELECT price_min, price_avg, price_max FROM wares WHERE ware_id = ?",
            (source_ware_id,),
        ).fetchone()
        conn2.close()
        if ware_row:
            price_min, price_avg, price_max = ware_row

    if price_avg and not price_min:
        price_min = int(price_avg * 0.85)
    if price_avg and not price_max:
        price_max = int(price_avg * 1.15)

    # Determine tags from source macro class
    tag_map: dict[str, str] = {
        "engine": "engine equipment",
        "shieldgenerator": "equipment shield",
        "weapon": "equipment weapon",
        "turret": "equipment turret",
        "missile": "equipment missile",
        "satellite": "equipment satellite",
        "navbeacon": "equipment navbeacon",
        "mine": "equipment mine",
    }
    tags = tag_map.get(macro_class, "equipment")

    if not description:
        description = f"A custom {name}"

    _make_wares_diff(
        out / "libraries" / "wares.xml",
        ware_id,
        f"{{{page_id},1}}",
        f"{{{page_id},2}}",
        transport="equipment",
        volume=1,
        tags=tags,
        price_min=price_min,
        price_avg=price_avg,
        price_max=price_max,
        component_ref=macro_id,
    )

    _make_translation(
        out / "t" / "0001-l044.xml",
        page_id,
        {1: name, 2: description},
        page_title=ware_id,
    )

    return [
        "libraries/wares.xml",
        "index/macros.xml",
        macro_file,
        "t/0001-l044.xml",
    ]


# --- Tier 3: scaffold ship ---

_SIZE_CLASS_MAP: dict[str, str] = {
    "s": "ship_s",
    "m": "ship_m",
    "l": "ship_l",
    "xl": "ship_xl",
}

_SIZE_DIR_MAP: dict[str, str] = {
    "s": "size_s",
    "m": "size_m",
    "l": "size_l",
    "xl": "size_xl",
}


def scaffold_ship(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Any = None,
    size: str = "s",
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = _DEFAULT_PAGE_ID,
) -> list[str]:
    """Scaffold a ship (Tier 3 — macro + index diffs + ware + translation).

    Requires ``clone_from`` to specify an existing ship macro to clone.
    The user must supply the component XML and 3D model separately.
    Returns a list of generated file paths (relative to output_dir).
    """
    _validate_id(macro_id, "macro_id")

    if not clone_from:
        raise ValueError("--clone-from is required for ship scaffolding")

    if db_path is None:
        raise ValueError("Index DB path is required for ship scaffolding")

    import pathlib

    out = pathlib.Path(output_dir)

    # Look up the source macro
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT value FROM macros WHERE name = ?", (clone_from,)).fetchone()
        if row is None:
            raise ValueError(f"Macro not found in index: {clone_from}")
        source_path = row[0]

        meta_row = conn.execute("SELECT value FROM meta WHERE key = 'game_dir'").fetchone()
    finally:
        conn.close()

    if meta_row is None:
        raise ValueError("Index does not contain game_dir metadata")

    game_dir = pathlib.Path(meta_row[0])

    # Read the source macro from VFS
    vfs = build_vfs(game_dir)
    vpath = source_path + ".xml"
    entry = _vfs_get_ci(vfs, vpath)
    if entry is None:
        raise ValueError(f"Macro file not found in VFS: {vpath}")

    source_data = _read_payload(entry)
    source_root = ET.fromstring(source_data)
    source_macro = source_root.find("macro")
    if source_macro is None:
        raise ValueError(f"No <macro> element in {vpath}")

    # Determine ship class and original component ref
    macro_class = source_macro.get("class", _SIZE_CLASS_MAP.get(size, "ship_s"))
    source_comp_elem = source_macro.find("component")
    original_comp_ref = source_comp_elem.get("ref", "") if source_comp_elem is not None else ""

    # Derive the component name for the new ship
    ware_id = macro_id.removesuffix("_macro")
    # Strip variant suffix (e.g., _a, _b) to get the base component name
    new_component = ware_id.rsplit("_", 1)[0] if "_" in ware_id else ware_id

    # Build new macro XML
    new_root = ET.Element("macros")
    new_macro = ET.SubElement(new_root, "macro", name=macro_id)
    new_macro.set("class", macro_class)
    ET.SubElement(new_macro, "component", ref=new_component)

    # Copy properties, update identification
    source_props = source_macro.find("properties")
    if source_props is not None:
        new_props = ET.SubElement(new_macro, "properties")
        for prop in source_props:
            new_prop = ET.SubElement(new_props, prop.tag, attrib=dict(prop.attrib))
            for sub in prop:
                new_sub = ET.SubElement(new_prop, sub.tag, attrib=dict(sub.attrib))
                for subsub in sub:
                    ET.SubElement(new_sub, subsub.tag, attrib=dict(subsub.attrib))
        ident = new_props.find("identification")
        if ident is not None:
            ident.set("name", f"{{{page_id},1}}")
            ident.set("description", f"{{{page_id},2}}")

    # Write macro file
    size_dir = _SIZE_DIR_MAP.get(size, "size_s")
    macro_rel = f"assets/units/{size_dir}/macros/{macro_id}"
    macro_file = f"{macro_rel}.xml"
    _write_xml(out / macro_file, new_root)

    # Index diff: register macro
    idx_diff = ET.Element("diff")
    idx_add = ET.SubElement(idx_diff, "add", sel="/index")
    ET.SubElement(
        idx_add,
        "entry",
        name=macro_id,
        value=macro_rel.replace("/", "\\"),
    )
    _write_xml(out / "index" / "macros.xml", idx_diff)

    # Index diff: register component (user supplies the actual file)
    comp_rel = f"assets/units/{size_dir}/{new_component}"
    cidx_diff = ET.Element("diff")
    cidx_add = ET.SubElement(cidx_diff, "add", sel="/index")
    ET.SubElement(
        cidx_add,
        "entry",
        name=new_component,
        value=comp_rel.replace("/", "\\"),
    )
    _write_xml(out / "index" / "components.xml", cidx_diff)

    # Derive prices
    if not price_avg:
        conn2 = sqlite3.connect(db_path)
        try:
            source_ware_id = clone_from.removesuffix("_macro")
            ware_row = conn2.execute(
                "SELECT price_min, price_avg, price_max FROM wares WHERE ware_id = ?",
                (source_ware_id,),
            ).fetchone()
        finally:
            conn2.close()
        if ware_row:
            price_min, price_avg, price_max = ware_row

    if price_avg and not price_min:
        price_min = int(price_avg * 0.85)
    if price_avg and not price_max:
        price_max = int(price_avg * 1.15)

    if not description:
        description = f"A custom {name}"

    _make_wares_diff(
        out / "libraries" / "wares.xml",
        ware_id,
        f"{{{page_id},1}}",
        f"{{{page_id},2}}",
        transport="ship",
        volume=1,
        tags="ship",
        price_min=price_min,
        price_avg=price_avg,
        price_max=price_max,
        component_ref=macro_id,
    )

    _make_translation(
        out / "t" / "0001-l044.xml",
        page_id,
        {1: name, 2: description},
        page_title=ware_id,
    )

    # Write a README note about what the user needs to supply
    readme = out / "README_SHIP.md"
    readme.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        f"# {name}\n\n"
        f"Scaffolded from `{clone_from}`.\n\n"
        f"## Do you need this?\n\n"
        f"If you only want to **modify an existing ship's stats** (hull, speed,\n"
        f"weapons, etc.), you do NOT need `scaffold ship`. Use this workflow\n"
        f"instead:\n\n"
        f"```bash\n"
        f"x4cat extract-macro {clone_from} -o ./base/\n"
        f"cp -r ./base ./modified\n"
        f"# edit the macro in ./modified\n"
        f"x4cat xmldiff --base ./base/{source_path}.xml \\\n"
        f"              --mod  ./modified/{source_path}.xml \\\n"
        f"              -o src/{source_path}.xml\n"
        f"```\n\n"
        f"This generates a diff patch that modifies the existing ship without\n"
        f"creating a new one — no 3D models or index registration needed.\n\n"
        f"## Adding a new ship\n\n"
        f"If you are creating an **entirely new ship**, you need to supply:\n\n"
        f"- `{comp_rel}.xml` — component file "
        f"(defines 3D geometry ref, connection points for weapons/engines/shields)\n"
        f"- `{comp_rel}_data/` — 3D model files (.xmf, .xpm, .xac)\n\n"
        f"These require Blender/3ds Max with Egosoft export plugins.\n\n"
        f"To reuse an existing ship's geometry instead, change the\n"
        f'`<component ref="..."/>` in the macro to reference the original\n'
        f"component (e.g., `{original_comp_ref or 'ship_arg_s_fighter_01'}`).\n"
        f"In that case you can delete `index/components.xml` from this scaffold.\n",
    )

    return [
        "libraries/wares.xml",
        "index/macros.xml",
        "index/components.xml",
        macro_file,
        "t/0001-l044.xml",
        "README_SHIP.md",
    ]
