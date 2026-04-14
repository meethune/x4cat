"""Tests for x4cat inspect."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from x4_catalog._index import build_index
from x4_catalog._inspect import inspect_asset

if TYPE_CHECKING:
    from pathlib import Path


def _make_game_dir(tmp_path: Path) -> Path:
    """Create a fake game dir with macros, components, wares, and a ship macro file."""
    from tests.conftest import _write_cat_dat

    game = tmp_path / "game"
    game.mkdir()

    import xml.etree.ElementTree as ET

    # index/macros.xml
    macros_root = ET.Element("index")
    ET.SubElement(
        macros_root,
        "entry",
        name="ship_test_macro",
        value=r"assets\units\size_s\macros\ship_test_macro",
    )
    macros_xml = ET.tostring(macros_root, encoding="unicode").encode()

    # index/components.xml
    comps_root = ET.Element("index")
    ET.SubElement(
        comps_root,
        "entry",
        name="ship_test",
        value=r"assets\units\size_s\ship_test",
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
        b'  <ware id="ship_test" name="{20101,100}" group="ships_argon"'
        b' transport="ship" volume="1" tags="ship">\n'
        b'    <price min="50000" average="75000" max="100000"/>\n'
        b'    <owner faction="argon"/>\n'
        b"  </ware>\n"
        b"</wares>"
    )

    # Ship macro XML
    ship_macro_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<macros>\n"
        b'  <macro name="ship_test_macro" class="ship_s">\n'
        b'    <component ref="ship_test"/>\n'
        b"    <properties>\n"
        b'      <identification name="{20101,100}" basename="{20101,99}"/>\n'
        b'      <hull max="3100"/>\n'
        b'      <storage missile="2"/>\n'
        b'      <purpose primary="fight"/>\n'
        b'      <ship type="fighter"/>\n'
        b'      <physics mass="6"/>\n'
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
            (
                "assets/units/size_s/macros/ship_test_macro.xml",
                ship_macro_xml,
                1000000,
            ),
        ],
    )
    return game


@pytest.fixture()
def indexed_game(tmp_path: Path) -> tuple[Path, Path]:
    """Build a game dir and index it. Returns (game_dir, db_path)."""
    game = _make_game_dir(tmp_path)
    db = tmp_path / "test.db"
    build_index(game, db)
    return game, db


class TestInspectAsset:
    def test_inspect_ware_by_id(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("energycells", db)
        assert result is not None
        assert result["ware_id"] == "energycells"
        assert result["price_avg"] == 16
        assert "argon" in result["owners"]
        assert "teladi" in result["owners"]

    def test_inspect_macro_by_id(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        assert result["macro_name"] == "ship_test_macro"
        assert "assets/units/size_s/macros/ship_test_macro" in result["macro_path"]

    def test_inspect_shows_component_ref(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        assert result.get("component_ref") == "ship_test"

    def test_inspect_shows_macro_properties(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        props = result.get("properties", {})
        assert props.get("hull.max") == "3100"
        assert props.get("ship.type") == "fighter"

    def test_inspect_ware_shows_macro_link(self, indexed_game: tuple[Path, Path]) -> None:
        result = inspect_asset("ship_test", indexed_game[1])
        assert result is not None
        assert result["ware_id"] == "ship_test"
        # Should find the linked macro
        assert result.get("macro_name") == "ship_test_macro"

    def test_inspect_nonexistent_returns_none(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("nonexistent_thing", db)
        assert result is None


class TestInspectCli:
    def test_inspect_subcommand(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "inspect",
                "energycells",
                "--db",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "energycells" in result.stdout
        assert "16" in result.stdout  # price_avg

    def test_inspect_macro(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "inspect",
                "ship_test_macro",
                "--db",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "ship_test_macro" in result.stdout
        assert "3100" in result.stdout  # hull

    def test_inspect_not_found(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "inspect",
                "nonexistent",
                "--db",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_inspect_auto_builds_index(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "auto.db"
        # No index exists yet — should auto-build with --game-dir
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "inspect",
                "energycells",
                "--game-dir",
                str(game),
                "--db",
                str(db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert db.exists()
        assert "energycells" in result.stdout
