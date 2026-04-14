"""Build and query a SQLite index of X4 game data for fast lookups."""

from __future__ import annotations

import hashlib
import logging
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from x4_catalog._core import CatEntry, _read_payload, build_vfs, iter_cat_files

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "x4cat"

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
    data = _read_payload(entry)
    root = ET.fromstring(data)
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
    data = _read_payload(entry)
    root = ET.fromstring(data)
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
    data = _read_payload(entry)
    root = ET.fromstring(data)
    count = 0
    for ware in root.findall("ware"):
        ware_id = ware.get("id", "")
        if not ware_id:
            continue
        price = ware.find("price")
        price_min = int(price.get("min", "0")) if price is not None else 0
        price_avg = int(price.get("average", "0")) if price is not None else 0
        price_max = int(price.get("max", "0")) if price is not None else 0

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
                int(ware.get("volume", "0")),
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

        conn.commit()
    finally:
        conn.close()

    logger.info(
        "Indexed %d macros, %d components, %d wares from %s",
        macro_count,
        comp_count,
        ware_count,
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
