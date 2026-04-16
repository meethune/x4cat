"""Build and query a SQLite index of X4 game data for fast lookups."""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from x4_catalog._core import CatEntry, build_vfs, iter_cat_files, read_payload
from x4_catalog._xml_utils import safe_fromstring

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "x4cat"


def _safe_int(val: str, default: int = 0) -> int:
    """Parse an integer from a string, returning *default* on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cat_files (
    cat_path TEXT PRIMARY KEY,
    size     INTEGER NOT NULL,
    mtime    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS macros (
    name  TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS components (
    name  TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wares (
    ware_id    TEXT PRIMARY KEY,
    name_ref   TEXT NOT NULL DEFAULT '',
    ware_group TEXT NOT NULL DEFAULT '',
    transport  TEXT NOT NULL DEFAULT '',
    volume     INTEGER NOT NULL DEFAULT 0,
    tags       TEXT NOT NULL DEFAULT '',
    price_min  INTEGER NOT NULL DEFAULT 0,
    price_avg  INTEGER NOT NULL DEFAULT 0,
    price_max  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ware_owners (
    ware_id TEXT NOT NULL,
    faction TEXT NOT NULL,
    PRIMARY KEY (ware_id, faction),
    FOREIGN KEY (ware_id) REFERENCES wares(ware_id)
);

CREATE TABLE IF NOT EXISTS macro_properties (
    macro_name    TEXT NOT NULL,
    property_key  TEXT NOT NULL,
    property_val  TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (macro_name, property_key),
    FOREIGN KEY (macro_name) REFERENCES macros(name)
);

CREATE TABLE IF NOT EXISTS translation_pages (
    page_id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS game_files (
    virtual_path TEXT PRIMARY KEY,
    size         INTEGER NOT NULL,
    mtime        INTEGER NOT NULL,
    md5          TEXT NOT NULL
);
"""


def db_path_for_game_dir(game_dir: Path) -> Path:
    """Return the default DB path for a game directory."""
    dir_hash = hashlib.sha256(str(game_dir.resolve()).encode()).hexdigest()[:16]
    return DEFAULT_CACHE_DIR / f"{dir_hash}.db"


def _record_cat_files(conn: sqlite3.Connection, game_dir: Path) -> None:
    """Record mtime and size of all .cat files for staleness detection."""
    for cat_path in iter_cat_files(game_dir):
        stat = cat_path.stat()
        conn.execute(
            "INSERT OR REPLACE INTO cat_files (cat_path, size, mtime) VALUES (?, ?, ?)",
            (str(cat_path), stat.st_size, stat.st_mtime),
        )


def _index_macros(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Index macros from index/macros.xml."""
    entry = vfs.get("index/macros.xml")
    if entry is None:
        return 0
    data = read_payload(entry)
    root = safe_fromstring(data)
    count = 0
    for e in root.findall("entry"):
        name = e.get("name", "")
        value = e.get("value", "").replace("\\", "/")
        if name:
            conn.execute(
                "INSERT OR REPLACE INTO macros (name, value) VALUES (?, ?)",
                (name, value),
            )
            count += 1
    return count


def _index_components(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Index components from index/components.xml."""
    entry = vfs.get("index/components.xml")
    if entry is None:
        return 0
    data = read_payload(entry)
    root = safe_fromstring(data)
    count = 0
    for e in root.findall("entry"):
        name = e.get("name", "")
        value = e.get("value", "").replace("\\", "/")
        if name:
            conn.execute(
                "INSERT OR REPLACE INTO components (name, value) VALUES (?, ?)",
                (name, value),
            )
            count += 1
    return count


def _index_wares(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Index wares from libraries/wares.xml."""
    entry = vfs.get("libraries/wares.xml")
    if entry is None:
        return 0
    data = read_payload(entry)
    root = safe_fromstring(data)
    count = 0
    for ware in root.findall("ware"):
        ware_id = ware.get("id", "")
        if not ware_id:
            continue
        price = ware.find("price")
        price_min = _safe_int(price.get("min", "0")) if price is not None else 0
        price_avg = _safe_int(price.get("average", "0")) if price is not None else 0
        price_max = _safe_int(price.get("max", "0")) if price is not None else 0

        conn.execute(
            "INSERT OR REPLACE INTO wares "
            "(ware_id, name_ref, ware_group, transport, volume, tags, "
            "price_min, price_avg, price_max) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ware_id,
                ware.get("name", ""),
                ware.get("group", ""),
                ware.get("transport", ""),
                _safe_int(ware.get("volume", "0")),
                ware.get("tags", ""),
                price_min,
                price_avg,
                price_max,
            ),
        )
        for owner in ware.findall("owner"):
            faction = owner.get("faction", "")
            if faction:
                conn.execute(
                    "INSERT OR REPLACE INTO ware_owners (ware_id, faction) VALUES (?, ?)",
                    (ware_id, faction),
                )
        count += 1
    return count


def _build_lower_vfs(vfs: dict[str, CatEntry]) -> dict[str, CatEntry]:
    """Build a lowercase-keyed index for case-insensitive lookups."""
    return {k.lower(): v for k, v in vfs.items()}


def vfs_get_ci(vfs: dict[str, CatEntry], path: str) -> CatEntry | None:
    """Case-insensitive VFS lookup (index paths may differ in casing from VFS)."""
    entry = vfs.get(path)
    if entry is not None:
        return entry
    path_lower = path.lower()
    for vpath, ent in vfs.items():
        if vpath.lower() == path_lower:
            return ent
    return None


def _index_macro_properties(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Scan individual macro files and index their properties."""
    lower_vfs = _build_lower_vfs(vfs)
    rows = conn.execute("SELECT name, value FROM macros").fetchall()
    count = 0
    for name, value in rows:
        vpath = value + ".xml"
        entry = lower_vfs.get(vpath.lower())
        if entry is None:
            continue
        try:
            data = read_payload(entry)
            root = safe_fromstring(data)
        except (OSError, ET.ParseError):
            continue
        macro = root.find("macro")
        if macro is None:
            continue
        # Store class attribute
        macro_class = macro.get("class", "")
        if macro_class:
            conn.execute(
                "INSERT OR REPLACE INTO macro_properties VALUES (?, ?, ?)",
                (name, "class", macro_class),
            )
        # Store component ref
        comp = macro.find("component")
        if comp is not None and comp.get("ref"):
            conn.execute(
                "INSERT OR REPLACE INTO macro_properties VALUES (?, ?, ?)",
                (name, "component_ref", comp.get("ref", "")),
            )
        # Store properties as element.attr keys
        props = macro.find("properties")
        if props is None:
            continue
        for elem in props:
            if elem.attrib:
                for attr, val in elem.attrib.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO macro_properties VALUES (?, ?, ?)",
                        (name, f"{elem.tag}.{attr}", val),
                    )
                count += 1
            elif elem.text and elem.text.strip():
                conn.execute(
                    "INSERT OR REPLACE INTO macro_properties VALUES (?, ?, ?)",
                    (name, elem.tag, elem.text.strip()),
                )
                count += 1
    return count


def _index_translation_pages(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Index base game translation page IDs for collision detection."""
    t_files = [k for k in vfs if k.startswith("t/") and k.endswith(".xml")]
    page_ids: set[int] = set()
    for vpath in t_files:
        try:
            data = read_payload(vfs[vpath])
            root = safe_fromstring(data)
        except (OSError, ET.ParseError):
            continue
        if root.tag != "language":
            continue
        for page in root.findall("page"):
            pid_str = page.get("id", "")
            if pid_str.isdigit():
                page_ids.add(int(pid_str))
    for pid in page_ids:
        conn.execute(
            "INSERT OR REPLACE INTO translation_pages (page_id) VALUES (?)",
            (pid,),
        )
    return len(page_ids)


def find_index_db() -> Path | None:
    """Find an existing index DB in the default cache directory.

    Returns the path to the most recently modified ``.db`` file,
    or ``None`` if no index exists.
    """
    if not DEFAULT_CACHE_DIR.exists():
        return None
    dbs = sorted(DEFAULT_CACHE_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime)
    return dbs[-1] if dbs else None


def _index_game_files(conn: sqlite3.Connection, vfs: dict[str, CatEntry]) -> int:
    """Index all VFS file entries for fast listing."""
    count = 0
    for vpath, entry in vfs.items():
        conn.execute(
            "INSERT OR REPLACE INTO game_files "
            "(virtual_path, size, mtime, md5) VALUES (?, ?, ?, ?)",
            (vpath, entry.size, entry.mtime, entry.md5),
        )
        count += 1
    return count


def _index_schemas(
    conn: sqlite3.Connection, vfs: dict[str, CatEntry], game_dir: Path
) -> dict[str, int]:
    """Extract XSD schemas and scriptproperties into the index."""
    import tempfile

    from x4_catalog._schema_extract import (
        extract_schema_to_db,
        extract_scriptproperties_to_db,
    )

    counts: dict[str, int] = {}

    # Extract XSD files to a temp dir for schema parsing
    xsd_paths = [k for k in vfs if k.endswith(".xsd")]
    if xsd_paths:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            for vpath in xsd_paths:
                entry = vfs[vpath]
                dest = (tmp / vpath).resolve()
                if not dest.is_relative_to(tmp.resolve()):
                    logger.warning("Skipping path traversal in XSD: %s", vpath)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(read_payload(entry))
            schema_counts = extract_schema_to_db(tmp, conn)
            counts.update(schema_counts)

    # Index scriptproperties.xml
    sp_entry = vfs.get("libraries/scriptproperties.xml")
    if sp_entry is not None:
        sp_data = read_payload(sp_entry)
        sp_counts = extract_scriptproperties_to_db(sp_data, conn)
        counts.update(sp_counts)

    return counts


def build_index(game_dir: Path, db_path: Path) -> Path:
    """Build a SQLite index from game files.

    Overwrites any existing database at *db_path*.
    Returns the path to the created database.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    vfs = build_vfs(game_dir)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_SCHEMA_SQL)

        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            ("game_dir", str(game_dir.resolve())),
        )

        _record_cat_files(conn, game_dir)
        macro_count = _index_macros(conn, vfs)
        comp_count = _index_components(conn, vfs)
        ware_count = _index_wares(conn, vfs)
        prop_count = _index_macro_properties(conn, vfs)
        tpage_count = _index_translation_pages(conn, vfs)
        file_count = _index_game_files(conn, vfs)
        _index_schemas(conn, vfs, game_dir)

        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Indexed %d macros, %d components, %d wares, %d properties, "
        "%d translation pages, %d files from %s",
        macro_count,
        comp_count,
        ware_count,
        prop_count,
        tpage_count,
        file_count,
        game_dir,
    )
    return db_path


def is_index_stale(game_dir: Path, db_path: Path) -> bool:
    """Check if the index is stale relative to the game's .cat files.

    Returns True if the DB doesn't exist, or if any .cat file has changed.
    """
    if not db_path.exists():
        return True

    conn = sqlite3.connect(db_path)
    try:
        recorded = {
            row[0]: (row[1], row[2])
            for row in conn.execute("SELECT cat_path, size, mtime FROM cat_files")
        }
    except sqlite3.OperationalError:
        return True
    finally:
        conn.close()

    current_cats = iter_cat_files(game_dir)
    if len(current_cats) != len(recorded):
        return True

    for cat_path in current_cats:
        key = str(cat_path)
        if key not in recorded:
            return True
        stat = cat_path.stat()
        rec_size, rec_mtime = recorded[key]
        if stat.st_size != rec_size or stat.st_mtime != rec_mtime:
            return True

    return False


def open_index(db_path: Path) -> sqlite3.Connection:
    """Open an existing index database.

    Raises ``FileNotFoundError`` if the database doesn't exist.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Index not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
