"""Tests for x4cat extract-macro."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from x4_catalog._extract_macro import extract_macro
from x4_catalog._index import build_index

if TYPE_CHECKING:
    from pathlib import Path


def _make_game_dir(tmp_path: Path) -> Path:
    """Create a fake game dir with a macro registered in the index."""
    from tests.conftest import _write_cat_dat

    game = tmp_path / "game"
    game.mkdir()

    import xml.etree.ElementTree as ET

    macros_root = ET.Element("index")
    ET.SubElement(
        macros_root,
        "entry",
        name="ship_test_macro",
        value=r"assets\units\size_s\macros\ship_test_macro",
    )
    macros_xml = ET.tostring(macros_root, encoding="unicode").encode()

    comps_root = ET.Element("index")
    comps_xml = ET.tostring(comps_root, encoding="unicode").encode()

    wares_xml = b'<?xml version="1.0" encoding="utf-8"?>\n<wares/>'

    ship_macro_xml = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b"<macros>\n"
        b'  <macro name="ship_test_macro" class="ship_s">\n'
        b'    <component ref="ship_test"/>\n'
        b"    <properties>\n"
        b'      <hull max="3100"/>\n'
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


class TestExtractMacro:
    def test_extract_by_id(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        result = extract_macro("ship_test_macro", db, game, out)
        assert result is not None
        assert result.exists()
        content = result.read_bytes()
        assert b"ship_test_macro" in content
        assert b"hull" in content

    def test_extract_preserves_path(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        extract_macro("ship_test_macro", db, game, out)
        expected = out / "assets" / "units" / "size_s" / "macros" / "ship_test_macro.xml"
        assert expected.exists()

    def test_extract_nonexistent_returns_none(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        result = extract_macro("nonexistent_macro", db, game, out)
        assert result is None

    def test_extract_creates_output_dir(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "nested" / "output"
        result = extract_macro("ship_test_macro", db, game, out)
        assert result is not None
        assert out.is_dir()


class TestExtractMacroCli:
    def test_extract_macro_subcommand(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "extract-macro",
                "ship_test_macro",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "assets" / "units" / "size_s" / "macros" / "ship_test_macro.xml").exists()

    def test_extract_macro_not_found(self, tmp_path: Path) -> None:
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
                "extract-macro",
                "nonexistent",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_extract_macro_with_prebuilt_index(self, tmp_path: Path) -> None:
        game = _make_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "extract-macro",
                "ship_test_macro",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
