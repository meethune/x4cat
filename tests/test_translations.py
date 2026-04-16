"""Tests for translation validation and scaffolding."""

from __future__ import annotations

import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from x4_catalog._translations import (
    scaffold_translation,
    validate_translations,
)

if TYPE_CHECKING:
    from pathlib import Path


def _xml(text: str) -> bytes:
    return textwrap.dedent(text).strip().encode()


def _make_mod(tmp_path: Path) -> Path:
    """Create a minimal mod directory with wares diff + translation."""
    mod = tmp_path / "mod"
    (mod / "libraries").mkdir(parents=True)
    (mod / "t").mkdir(parents=True)

    (mod / "libraries" / "wares.xml").write_bytes(
        _xml("""\
        <?xml version="1.0" encoding="utf-8"?>
        <diff>
          <add sel="/wares">
            <ware id="mymod_fuel" name="{90001,1}"
                  description="{90001,2}" group="energy"/>
          </add>
        </diff>
    """)
    )

    (mod / "t" / "0001-l044.xml").write_bytes(
        _xml("""\
        <?xml version="1.0" encoding="utf-8"?>
        <language id="44">
          <page id="90001" title="My Mod">
            <t id="1">Custom Fuel</t>
            <t id="2">A custom fuel type</t>
          </page>
        </language>
    """)
    )
    return mod


# --- validate_translations ---


class TestValidateTranslations:
    def test_clean_mod_no_errors(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        result = validate_translations(mod)
        assert result["errors"] == []

    def test_missing_translation_detected(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        # Add a reference to an undefined entry
        wares = mod / "libraries" / "wares.xml"
        wares.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="mymod_fuel" name="{90001,1}"
                      description="{90001,99}" group="energy"/>
              </add>
            </diff>
        """)
        )
        result = validate_translations(mod)
        errors = result["errors"]
        assert len(errors) >= 1
        assert any("90001" in e and "99" in e for e in errors)

    def test_orphaned_translation_warned(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        # Add an entry that nothing references
        t_file = mod / "t" / "0001-l044.xml"
        t_file.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Custom Fuel</t>
                <t id="2">A custom fuel type</t>
                <t id="99">Nobody uses this</t>
              </page>
            </language>
        """)
        )
        result = validate_translations(mod)
        warnings = result["warnings"]
        assert any("90001" in w and "99" in w for w in warnings)

    def test_page_id_collision_warned(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        # Use a base-game page ID
        wares = mod / "libraries" / "wares.xml"
        wares.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="mymod_fuel" name="{1001,1}" group="energy"/>
              </add>
            </diff>
        """)
        )
        (mod / "t" / "0001-l044.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="1001" title="Collision">
                <t id="1">Bad</t>
              </page>
            </language>
        """)
        )
        result = validate_translations(mod)
        warnings = result["warnings"]
        assert any("1001" in w and "collide" in w.lower() for w in warnings)

    def test_page_id_collision_from_index(self, tmp_path: Path) -> None:
        """Collision detection using actual base game page IDs from the index."""
        from tests.conftest import _write_cat_dat
        from x4_catalog._index import build_index

        # Create a game dir with a translation file containing page 5001
        game = tmp_path / "game"
        game.mkdir()
        game_t = (
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<language id="44">\n'
            b'  <page id="5001" title="Game Text">\n'
            b'    <t id="1">Game text</t>\n'
            b"  </page>\n"
            b"</language>"
        )
        idx = b"<index/>"
        wares = b"<wares/>"
        _write_cat_dat(
            game,
            "01.cat",
            [
                ("t/0001-l044.xml", game_t, 1000000),
                ("index/macros.xml", idx, 1000000),
                ("index/components.xml", idx, 1000000),
                ("libraries/wares.xml", wares, 1000000),
            ],
        )
        db = tmp_path / "test.db"
        build_index(game, db)

        # Create a mod that uses page 5001 (collision)
        mod = tmp_path / "mod"
        (mod / "libraries").mkdir(parents=True)
        (mod / "t").mkdir(parents=True)
        (mod / "libraries" / "wares.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="x" name="{5001,1}" group="energy"/>
              </add>
            </diff>
        """)
        )
        (mod / "t" / "0001-l044.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="5001" title="Bad">
                <t id="1">Collides</t>
              </page>
            </language>
        """)
        )
        result = validate_translations(mod, db_path=db)
        warnings = result["warnings"]
        assert any("5001" in w and "collide" in w.lower() for w in warnings)

    def test_no_translation_files_with_refs(self, tmp_path: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "libraries").mkdir(parents=True)
        (mod / "libraries" / "wares.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="mymod_fuel" name="{90001,1}" group="energy"/>
              </add>
            </diff>
        """)
        )
        result = validate_translations(mod)
        assert len(result["errors"]) >= 1

    def test_no_refs_no_translations_clean(self, tmp_path: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "script.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <mdscript name="Test">
              <cues>
                <cue name="Start">
                  <actions>
                    <debug_text text="'no refs here'" filter="general"/>
                  </actions>
                </cue>
              </cues>
            </mdscript>
        """)
        )
        result = validate_translations(mod)
        assert result["errors"] == []
        assert result["warnings"] == []

    def test_inconsistent_entries_across_languages(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        # Add a German file missing entry 2
        (mod / "t" / "0001-l049.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="49">
              <page id="90001" title="My Mod">
                <t id="1">Kraftstoff</t>
              </page>
            </language>
        """)
        )
        result = validate_translations(mod)
        warnings = result["warnings"]
        assert any("49" in w and "90001" in w for w in warnings)

    def test_non_mod_refs_ignored(self, tmp_path: Path) -> None:
        """Refs to base game page IDs (< 90000) in diff patches are not
        expected to have local translations — they use base game text."""
        mod = tmp_path / "mod"
        (mod / "libraries").mkdir(parents=True)
        (mod / "libraries" / "wares.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/wares/ware[@id='energycells']/@name">
                {20201,301}
              </replace>
            </diff>
        """)
        )
        result = validate_translations(mod)
        # Base game refs should not cause missing translation errors
        assert result["errors"] == []


# --- scaffold_translation ---


class TestScaffoldTranslation:
    def test_generates_stub(self, tmp_path: Path) -> None:
        source = tmp_path / "source.xml"
        source.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Custom Fuel</t>
                <t id="2">A custom fuel type</t>
              </page>
            </language>
        """)
        )
        out = tmp_path / "0001-l049.xml"
        scaffold_translation(source, out, lang_code=49)
        assert out.exists()

    def test_stub_has_correct_language_id(self, tmp_path: Path) -> None:
        source = tmp_path / "source.xml"
        source.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Hello</t>
              </page>
            </language>
        """)
        )
        out = tmp_path / "0001-l049.xml"
        scaffold_translation(source, out, lang_code=49)
        root = ET.parse(out).getroot()
        assert root.get("id") == "49"

    def test_stub_preserves_page_structure(self, tmp_path: Path) -> None:
        source = tmp_path / "source.xml"
        source.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Name</t>
                <t id="2">Description</t>
                <t id="3">Tooltip</t>
              </page>
            </language>
        """)
        )
        out = tmp_path / "0001-l033.xml"
        scaffold_translation(source, out, lang_code=33)
        root = ET.parse(out).getroot()
        page = root.find("page")
        assert page is not None
        assert page.get("id") == "90001"
        entries = page.findall("t")
        assert len(entries) == 3

    def test_stub_marks_entries_for_translation(self, tmp_path: Path) -> None:
        source = tmp_path / "source.xml"
        source.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Custom Fuel</t>
              </page>
            </language>
        """)
        )
        out = tmp_path / "0001-l049.xml"
        scaffold_translation(source, out, lang_code=49)
        root = ET.parse(out).getroot()
        t = root.find(".//t[@id='1']")
        assert t is not None
        assert t.text is not None
        assert "Custom Fuel" in t.text or "TRANSLATE" in t.text


# --- CLI ---


class TestTranslationsCli:
    def test_validate_translations_pass(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "validate-translations",
                str(mod),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_validate_translations_fail(self, tmp_path: Path) -> None:
        mod = _make_mod(tmp_path)
        (mod / "libraries" / "wares.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="x" name="{90001,99}" group="energy"/>
              </add>
            </diff>
        """)
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "validate-translations",
                str(mod),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "missing" in result.stdout.lower() or "MISSING" in result.stdout

    def test_scaffold_translation_cli(self, tmp_path: Path) -> None:
        source = tmp_path / "source.xml"
        source.write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <language id="44">
              <page id="90001" title="My Mod">
                <t id="1">Hello</t>
              </page>
            </language>
        """)
        )
        out = tmp_path / "0001-l049.xml"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "scaffold",
                "translation",
                "--from",
                str(source),
                "--lang",
                "49",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out.exists()
