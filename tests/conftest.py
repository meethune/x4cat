"""Shared fixtures and helpers for X4 catalog tests."""

from __future__ import annotations

import hashlib
import sqlite3
import textwrap
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def create_index_db(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection with the full x4cat index schema applied."""
    from x4_catalog._index import _SCHEMA_SQL

    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA_SQL)
    return conn


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _xml(text: str) -> bytes:
    """Dedent and encode XML text."""
    return textwrap.dedent(text).strip().encode()


def _write_cat_dat(
    directory: Path,
    cat_name: str,
    entries: list[tuple[str, bytes, int]],
) -> None:
    """Write a paired .cat/.dat file.

    entries: list of (virtual_path, content_bytes, mtime).
    """
    cat_lines: list[str] = []
    dat_blob = bytearray()
    for vpath, content, mtime in entries:
        cat_lines.append(f"{vpath} {len(content)} {mtime} {_md5(content)}")
        dat_blob.extend(content)
    (directory / cat_name).write_text("\n".join(cat_lines) + "\n", encoding="utf-8")
    (directory / cat_name.replace(".cat", ".dat")).write_bytes(bytes(dat_blob))


@pytest.fixture()
def game_dir(tmp_path: Path) -> Path:
    """Minimal fake game install with two numbered catalogs.

    01.cat/dat has: md/test.xml, libraries/wares.xml
    02.cat/dat has: md/test.xml (override), aiscripts/order.trade.xml
    """
    _write_cat_dat(
        tmp_path,
        "01.cat",
        [
            ("md/test.xml", b"<md>original</md>", 1000000),
            ("libraries/wares.xml", b"<wares/>", 1000001),
        ],
    )
    _write_cat_dat(
        tmp_path,
        "02.cat",
        [
            ("md/test.xml", b"<md>updated</md>", 2000000),
            ("aiscripts/order.trade.xml", b"<aiscript/>", 2000001),
        ],
    )
    return tmp_path


@pytest.fixture()
def ext_dir(game_dir: Path) -> Path:
    """Add a DLC-like extension to the game dir."""
    ext = game_dir / "extensions" / "ego_dlc_test"
    ext.mkdir(parents=True)
    (ext / "content.xml").write_text(
        '<?xml version="1.0"?>\n'
        '<content id="ego_dlc_test" name="Test DLC" version="100">\n'
        '  <dependency version="100" />\n'
        "</content>\n",
        encoding="utf-8",
    )
    _write_cat_dat(
        ext,
        "ext_01.cat",
        [
            ("md/dlc_mission.xml", b"<md>dlc</md>", 3000000),
            ("libraries/wares.xml", b"<wares>dlc</wares>", 3000001),
        ],
    )
    return ext


def make_indexed_game_dir(tmp_path: Path) -> tuple[Path, Path]:
    """Create a comprehensive fake game dir with index.

    Includes macros (ship + engine), components, wares with owners,
    and ship/engine macro XML files. Returns ``(game_dir, db_path)``.

    This is the canonical test fixture — use instead of per-test
    ``_make_game_dir`` helpers.
    """
    game = tmp_path / "game"
    game.mkdir()

    # index/macros.xml
    idx_macros = ET.Element("index")
    ET.SubElement(
        idx_macros,
        "entry",
        name="ship_test_macro",
        value=r"assets\units\size_s\macros\ship_test_macro",
    )
    ET.SubElement(
        idx_macros,
        "entry",
        name="ship_test_s_fighter_01_a_macro",
        value=r"assets\units\size_s\macros\ship_test_s_fighter_01_a_macro",
    )
    ET.SubElement(
        idx_macros,
        "entry",
        name="engine_test_mk1_macro",
        value=r"assets\props\engines\macros\engine_test_mk1_macro",
    )
    ET.SubElement(
        idx_macros,
        "entry",
        name="weapon_test_macro",
        value=r"assets\props\WeaponSystems\macros\weapon_test_macro",
    )
    macros_xml = ET.tostring(idx_macros, encoding="unicode").encode()

    # index/components.xml
    idx_comps = ET.Element("index")
    ET.SubElement(
        idx_comps,
        "entry",
        name="ship_test",
        value=r"assets\units\size_s\ship_test",
    )
    ET.SubElement(
        idx_comps,
        "entry",
        name="ship_test_s_fighter_01",
        value=r"assets\units\size_s\ship_test_s_fighter_01",
    )
    ET.SubElement(
        idx_comps,
        "entry",
        name="engine_test_mk1",
        value=r"assets\props\engines\engine_test_mk1",
    )
    comps_xml = ET.tostring(idx_comps, encoding="unicode").encode()

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
        b'  <ware id="ship_test" name="{20101,100}" group="ships_argon"'
        b' transport="ship" volume="1" tags="ship">\n'
        b'    <price min="50000" average="75000" max="100000"/>\n'
        b'    <component ref="ship_test_macro"/>\n'
        b'    <owner faction="argon"/>\n'
        b"  </ware>\n"
        b'  <ware id="engine_test_mk1" name="{20107,100}"'
        b' group="engines" transport="equipment"'
        b' volume="1" tags="engine equipment">\n'
        b'    <price min="1000" average="1500" max="2000"/>\n'
        b'    <component ref="engine_test_mk1_macro"/>\n'
        b'    <owner faction="argon"/>\n'
        b"  </ware>\n"
        b'  <ware id="ship_test_s_fighter_01_a" name="{20101,200}"'
        b' transport="ship" volume="1" tags="ship">\n'
        b'    <price min="100000" average="130000" max="160000"/>\n'
        b'    <component ref="ship_test_s_fighter_01_a_macro"/>\n'
        b'    <owner faction="argon"/>\n'
        b"  </ware>\n"
        b'  <ware id="advancedcomposites" name="{20201,401}" group="hightech"'
        b' transport="container" volume="32" tags="container economy">\n'
        b'    <price min="432" average="540" max="648"/>\n'
        b"  </ware>\n"
        b"</wares>"
    )

    # Ship macro XML
    ship_macro = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<macros>\n"
        b'  <macro name="ship_test_macro" class="ship_s">\n'
        b'    <component ref="ship_test"/>\n'
        b"    <properties>\n"
        b'      <identification name="{20101,100}" basename="{20101,99}"/>\n'
        b'      <hull max="3100"/>\n'
        b'      <purpose primary="fight"/>\n'
        b'      <ship type="fighter"/>\n'
        b'      <physics mass="6"/>\n'
        b"    </properties>\n"
        b"  </macro>\n"
        b"</macros>"
    )

    ship_fighter_macro = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<macros>\n"
        b'  <macro name="ship_test_s_fighter_01_a_macro" class="ship_s">\n'
        b'    <component ref="ship_test_s_fighter_01"/>\n'
        b"    <properties>\n"
        b'      <identification name="{20101,200}" basename="{20101,199}"'
        b' makerrace="argon" description="{20101,202}"/>\n'
        b'      <hull max="3100"/>\n'
        b'      <purpose primary="fight"/>\n'
        b'      <ship type="fighter"/>\n'
        b"    </properties>\n"
        b"  </macro>\n"
        b"</macros>"
    )

    # Engine macro XML
    engine_macro = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<macros>\n"
        b'  <macro name="engine_test_mk1_macro" class="engine">\n'
        b'    <component ref="engine_test_mk1"/>\n'
        b"    <properties>\n"
        b'      <identification name="{20107,100}" mk="1"/>\n'
        b'      <boost duration="10" thrust="5.0"/>\n'
        b'      <travel charge="15" thrust="20.0"/>\n'
        b'      <hull max="500"/>\n'
        b"    </properties>\n"
        b"  </macro>\n"
        b"</macros>"
    )

    _write_cat_dat(
        game,
        "01.cat",
        [
            ("index/macros.xml", macros_xml, 1000000),
            ("index/components.xml", comps_xml, 1000000),
            ("libraries/wares.xml", wares_xml, 1000000),
            ("assets/units/size_s/macros/ship_test_macro.xml", ship_macro, 1000000),
            (
                "assets/units/size_s/macros/ship_test_s_fighter_01_a_macro.xml",
                ship_fighter_macro,
                1000000,
            ),
            (
                "assets/props/engines/macros/engine_test_mk1_macro.xml",
                engine_macro,
                1000000,
            ),
        ],
    )

    from x4_catalog._index import build_index

    db = tmp_path / "test.db"
    build_index(game, db)
    return game, db
