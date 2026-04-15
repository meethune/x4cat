"""Tests for game data index."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from x4_catalog._index import (
    DEFAULT_CACHE_DIR,
    build_index,
    db_path_for_game_dir,
    is_index_stale,
    open_index,
)

if TYPE_CHECKING:
    from pathlib import Path


def _make_game_dir(tmp_path: Path) -> Path:
    """Create a minimal fake game dir with index/macros, index/components, and wares."""
    from tests.conftest import _write_cat_dat

    game = tmp_path / "game"
    game.mkdir()

    import xml.etree.ElementTree as ET

    # index/macros.xml
    macros_root = ET.Element("index")
    ET.SubElement(
        macros_root,
        "entry",
        name="ship_arg_s_fighter_01_a_macro",
        value=r"assets\units\size_s\macros\ship_arg_s_fighter_01_a_macro",
    )
    ET.SubElement(
        macros_root,
        "entry",
        name="weapon_test_macro",
        value=r"assets\props\WeaponSystems\macros\weapon_test_macro",
    )
    macros_xml = ET.tostring(macros_root, encoding="unicode").encode()

    # index/components.xml
    comps_root = ET.Element("index")
    ET.SubElement(
        comps_root,
        "entry",
        name="ship_arg_s_fighter_01",
        value=r"assets\units\size_s\ship_arg_s_fighter_01",
    )
    comps_xml = ET.tostring(comps_root, encoding="unicode").encode()

    # libraries/wares.xml
    wares_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<wares>\n"
        b'  <ware id="energycells" name="{20201,301}" group="energy"'
        b' transport="container" volume="6" tags="container economy">\n'
        b'    <price min="10" average="16" max="22"/>\n'
        b'    <owner faction="argon"/>\n'
        b'    <owner faction="teladi"/>\n'
        b"  </ware>\n"
        b'  <ware id="ship_arg_s_fighter_01_a" name="{20101,10302}"'
        b' group="ships_argon" transport="ship" volume="1" tags="ship">\n'
        b'    <price min="50000" average="75000" max="100000"/>\n'
        b'    <owner faction="argon"/>\n'
        b"  </ware>\n"
        b"</wares>"
    )

    # Ship macro XML
    ship_macro_xml = b"""\
<?xml version="1.0" encoding="utf-8"?>
<macros>
  <macro name="ship_arg_s_fighter_01_a_macro" class="ship_s">
    <component ref="ship_arg_s_fighter_01"/>
    <properties>
      <hull max="3100"/>
    </properties>
  </macro>
</macros>"""

    _write_cat_dat(
        game,
        "01.cat",
        [
            ("index/macros.xml", macros_xml, 1000000),
            ("index/components.xml", comps_xml, 1000000),
            ("libraries/wares.xml", wares_xml, 1000000),
            (
                "assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml",
                ship_macro_xml,
                1000000,
            ),
        ],
    )
    return game


class TestBuildIndex:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        assert db.exists()

    def test_macros_table_populated(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT name, value FROM macros").fetchall()
        conn.close()
        names = {r[0] for r in rows}
        assert "ship_arg_s_fighter_01_a_macro" in names
        assert "weapon_test_macro" in names

    def test_components_table_populated(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT name, value FROM components").fetchall()
        conn.close()
        assert any(r[0] == "ship_arg_s_fighter_01" for r in rows)

    def test_wares_table_populated(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT ware_id, name_ref, ware_group FROM wares").fetchall()
        conn.close()
        ids = {r[0] for r in rows}
        assert "energycells" in ids
        assert "ship_arg_s_fighter_01_a" in ids

    def test_ware_owners_table_populated(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT faction FROM ware_owners WHERE ware_id = 'energycells'"
        ).fetchall()
        conn.close()
        factions = {r[0] for r in rows}
        assert factions == {"argon", "teladi"}

    def test_ware_prices_stored(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT price_min, price_avg, price_max FROM wares WHERE ware_id = 'energycells'"
        ).fetchone()
        conn.close()
        assert row == (10, 16, 22)

    def test_meta_table_has_game_dir(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        row = conn.execute("SELECT value FROM meta WHERE key = 'game_dir'").fetchone()
        conn.close()
        assert row is not None
        assert str(game) in row[0]

    def test_translation_pages_indexed(self, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        game = tmp_path / "game_with_t"
        game.mkdir()
        t_xml = (
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<language id="44">\n'
            b'  <page id="1001" title="Interface"><t id="1">Hull</t></page>\n'
            b'  <page id="20201" title="Wares"><t id="1">Energy</t></page>\n'
            b"</language>"
        )
        idx = b"<index/>"
        wares = b"<wares/>"
        _write_cat_dat(
            game,
            "01.cat",
            [
                ("t/0001-l044.xml", t_xml, 1000000),
                ("index/macros.xml", idx, 1000000),
                ("index/components.xml", idx, 1000000),
                ("libraries/wares.xml", wares, 1000000),
            ],
        )
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT page_id FROM translation_pages").fetchall()
        conn.close()
        page_ids = {r[0] for r in rows}
        assert 1001 in page_ids
        assert 20201 in page_ids

    def test_cat_checksums_stored(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = sqlite3.connect(db)
        rows = conn.execute("SELECT cat_path FROM cat_files").fetchall()
        conn.close()
        assert len(rows) >= 1


class TestStalenessDetection:
    def test_fresh_index_not_stale(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        assert not is_index_stale(game, db)

    def test_modified_cat_detected_as_stale(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        # Modify the cat file
        cat = game / "01.cat"
        cat.write_text(cat.read_text() + "\n")
        assert is_index_stale(game, db)

    def test_missing_db_detected_as_stale(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "nonexistent.db"
        assert is_index_stale(game, db)


class TestDbPathForGameDir:
    def test_deterministic(self, tmp_path: Path) -> None:
        p1 = db_path_for_game_dir(tmp_path / "game")
        p2 = db_path_for_game_dir(tmp_path / "game")
        assert p1 == p2

    def test_different_dirs_different_paths(self, tmp_path: Path) -> None:
        p1 = db_path_for_game_dir(tmp_path / "game1")
        p2 = db_path_for_game_dir(tmp_path / "game2")
        assert p1 != p2

    def test_under_cache_dir(self, tmp_path: Path) -> None:
        p = db_path_for_game_dir(tmp_path / "some_game")
        assert str(DEFAULT_CACHE_DIR) in str(p)


class TestOpenIndex:
    def test_returns_connection(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        conn = open_index(db)
        assert conn is not None
        rows = conn.execute("SELECT COUNT(*) FROM wares").fetchone()
        assert rows[0] > 0
        conn.close()

    def test_missing_db_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            open_index(tmp_path / "nonexistent.db")


class TestRefreshFlag:
    def test_rebuild_overwrites_existing(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        # Modify and rebuild
        (game / "01.cat").write_text((game / "01.cat").read_text() + "\n")
        build_index(game, db)
        assert not is_index_stale(game, db)


# --- CLI ---


class TestIndexCli:
    def test_index_subcommand(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "index",
                str(game),
                "-o",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert db.exists()

    def test_index_reports_counts(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "index",
                str(game),
                "-o",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert "macro" in result.stdout.lower()
        assert "ware" in result.stdout.lower()

    def test_index_refresh(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        # Build twice
        subprocess.run(
            [sys.executable, "-m", "x4_catalog", "index", str(game), "-o", str(db)],
            capture_output=True,
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "index",
                str(game),
                "-o",
                str(db),
                "--refresh",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
