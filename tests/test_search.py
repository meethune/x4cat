"""Tests for x4cat search."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from x4_catalog._index import build_index
from x4_catalog._search import search_assets

if TYPE_CHECKING:
    from pathlib import Path


def _make_game_dir(tmp_path: Path) -> Path:
    """Create a fake game dir with searchable content."""
    from tests.conftest import _write_cat_dat

    game = tmp_path / "game"
    game.mkdir()

    import xml.etree.ElementTree as ET

    macros_root = ET.Element("index")
    s = r"assets\units\size_s\macros"
    m = r"assets\units\size_m\macros"
    p = r"assets\props"
    macro_entries = [
        ("ship_arg_s_fighter_01_a_macro", f"{s}\\ship_arg_s_fighter_01_a_macro"),
        ("ship_arg_m_frigate_01_a_macro", f"{m}\\ship_arg_m_frigate_01_a_macro"),
        ("weapon_gen_s_laser_01_mk1_macro", f"{p}\\weapons\\weapon_gen_s_laser_01_mk1_macro"),
        ("engine_arg_s_travel_01_mk1_macro", f"{p}\\engines\\engine_arg_s_travel_01_mk1_macro"),
    ]
    for name, value in macro_entries:
        ET.SubElement(macros_root, "entry", name=name, value=value)
    macros_xml = ET.tostring(macros_root, encoding="unicode").encode()

    comps_root = ET.Element("index")
    ET.SubElement(
        comps_root,
        "entry",
        name="ship_arg_s_fighter_01",
        value=r"assets\units\size_s\ship_arg_s_fighter_01",
    )
    comps_xml = ET.tostring(comps_root, encoding="unicode").encode()

    wares_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<wares>\n"
        b'  <ware id="energycells" name="{20201,301}" group="energy"'
        b' transport="container" volume="6" tags="container economy">\n'
        b'    <price min="10" average="16" max="22"/>\n'
        b"  </ware>\n"
        b'  <ware id="ship_arg_s_fighter_01_a" name="{20101,100}"'
        b' group="ships_argon" transport="ship" volume="1" tags="ship">\n'
        b'    <price min="50000" average="75000" max="100000"/>\n'
        b"  </ware>\n"
        b'  <ware id="advancedcomposites" name="{20201,401}" group="hightech"'
        b' transport="container" volume="32" tags="container economy">\n'
        b'    <price min="432" average="540" max="648"/>\n'
        b"  </ware>\n"
        b"</wares>"
    )

    _write_cat_dat(
        game,
        "01.cat",
        [
            ("index/macros.xml", macros_xml, 1000000),
            ("index/components.xml", comps_xml, 1000000),
            ("libraries/wares.xml", wares_xml, 1000000),
        ],
    )
    return game


class TestSearchAssets:
    def test_search_by_partial_id(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db)
        ids = {r["id"] for r in results}
        assert "ship_arg_s_fighter_01_a_macro" in ids
        assert "ship_arg_s_fighter_01_a" in ids  # ware
        assert "ship_arg_s_fighter_01" in ids  # component

    def test_search_no_match(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("nonexistent_xyz", db)
        assert results == []

    def test_search_by_group(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("hightech", db)
        ids = {r["id"] for r in results}
        assert "advancedcomposites" in ids

    def test_search_by_tag(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("economy", db)
        ids = {r["id"] for r in results}
        assert "energycells" in ids

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results_lower = search_assets("fighter", db)
        results_upper = search_assets("FIGHTER", db)
        assert len(results_lower) == len(results_upper)

    def test_search_results_have_type(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db)
        types = {r["type"] for r in results}
        assert "macro" in types
        assert "ware" in types
        assert "component" in types

    def test_search_results_have_path(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("laser", db)
        macro_results = [r for r in results if r["type"] == "macro"]
        assert macro_results
        assert macro_results[0]["path"]

    def test_search_type_filter(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db, type_filter="ware")
        assert all(r["type"] == "ware" for r in results)
        assert len(results) >= 1


class TestSearchCli:
    def test_search_subcommand(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "--db", str(db), "search", "fighter"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "fighter" in result.stdout.lower()

    def test_search_no_results(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "--db", str(db), "search", "zzzznotfound"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0" in result.stdout

    def test_search_with_type_filter(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "search",
                "fighter",
                "--type",
                "macro",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "macro" in result.stdout.lower()

    def test_search_no_index_errors(self, tmp_path: Path) -> None:
        db = tmp_path / "nonexistent.db"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "search",
                "energy",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
