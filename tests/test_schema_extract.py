"""Tests for XSD schema extraction and structural validation."""

from __future__ import annotations

import sqlite3
import textwrap
import time
from pathlib import Path

import pytest

from x4_catalog._schema_extract import (
    extract_schema_to_db,
    extract_scriptproperties_to_db,
)

_GAME_DIR = Path("/mnt/c/Games/steamapps/common/X4 Foundations")
_HAS_GAME = _GAME_DIR.exists()


def _xml(text: str) -> bytes:
    return textwrap.dedent(text).strip().encode()


@pytest.fixture()
def schema_dir(tmp_path: Path) -> Path:
    """Extract XSD schemas from game files to a temp dir."""
    if not _HAS_GAME:
        pytest.skip("Game files not available")
    from x4_catalog import extract_to_disk

    extract_to_disk(_GAME_DIR, tmp_path / "schemas", glob_pattern="*.xsd")
    return tmp_path / "schemas"


# --- Phase 1: XSD extraction ---


class TestSchemaExtraction:
    def test_extraction_is_fast(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        t0 = time.time()
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        elapsed = time.time() - t0
        conn.close()
        print(f"Extraction time: {elapsed:.2f}s")
        assert elapsed < 5.0

    def test_actions_group_resolves(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        rows = conn.execute(
            "SELECT COUNT(*) FROM schema_groups WHERE group_name = 'actions'"
        ).fetchone()
        conn.close()
        assert rows[0] > 400

    def test_commonactions_group_resolves(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        rows = conn.execute(
            "SELECT COUNT(*) FROM schema_groups WHERE group_name = 'commonactions'"
        ).fetchone()
        conn.close()
        assert rows[0] > 700

    def test_enumerations_extracted(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        rows = conn.execute("SELECT COUNT(DISTINCT type_name) FROM schema_enumerations").fetchone()
        conn.close()
        assert rows[0] > 5

    def test_attributes_extracted(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        rows = conn.execute("SELECT COUNT(*) FROM schema_attributes").fetchone()
        conn.close()
        assert rows[0] > 50

    def test_signal_cue_is_valid_action(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        # signal_cue is in md.xsd's specificactions, resolved into actions
        row = conn.execute(
            "SELECT 1 FROM schema_groups "
            "WHERE group_name = 'actions' AND element_name = 'signal_cue'"
        ).fetchone()
        conn.close()
        assert row is not None

    def test_debug_text_is_valid_action(self, schema_dir: Path, tmp_path: Path) -> None:
        db = tmp_path / "schema.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(schema_dir, conn)
        conn.commit()
        row = conn.execute(
            "SELECT 1 FROM schema_groups "
            "WHERE group_name = 'actions' AND element_name = 'debug_text'"
        ).fetchone()
        conn.close()
        assert row is not None


# --- Synthetic tests (no game files needed) ---


class TestSyntheticExtraction:
    def test_simple_xsd(self, tmp_path: Path) -> None:
        xsd_dir = tmp_path / "schemas" / "libraries"
        xsd_dir.mkdir(parents=True)
        (xsd_dir / "common.xsd").write_text(
            '<?xml version="1.0"?>\n'
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
            '  <xs:simpleType name="myenum">\n'
            '    <xs:restriction base="xs:string">\n'
            '      <xs:enumeration value="a"/>\n'
            '      <xs:enumeration value="b"/>\n'
            "    </xs:restriction>\n"
            "  </xs:simpleType>\n"
            '  <xs:group name="myactions">\n'
            "    <xs:choice>\n"
            '      <xs:element name="do_something"/>\n'
            '      <xs:element name="do_other"/>\n'
            "    </xs:choice>\n"
            "  </xs:group>\n"
            '  <xs:attributeGroup name="myattrs">\n'
            '    <xs:attribute name="value" type="xs:string" use="required"/>\n'
            "  </xs:attributeGroup>\n"
            "</xs:schema>"
        )
        (xsd_dir / "md.xsd").write_text(
            '<?xml version="1.0"?>\n'
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
            '  <xs:include schemaLocation="common.xsd"/>\n'
            '  <xs:group name="allactions">\n'
            "    <xs:choice>\n"
            '      <xs:element name="custom_action"/>\n'
            '      <xs:group ref="myactions"/>\n'
            "    </xs:choice>\n"
            "  </xs:group>\n"
            "</xs:schema>"
        )

        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        extract_schema_to_db(tmp_path / "schemas", conn)
        conn.commit()

        # allactions should resolve to: custom_action + do_something + do_other
        rows = conn.execute(
            "SELECT element_name FROM schema_groups "
            "WHERE group_name = 'allactions' ORDER BY element_name"
        ).fetchall()
        names = [r[0] for r in rows]
        assert "custom_action" in names
        assert "do_something" in names
        assert "do_other" in names

        # Enumerations
        rows = conn.execute(
            "SELECT value FROM schema_enumerations WHERE type_name = 'myenum' ORDER BY value"
        ).fetchall()
        assert [r[0] for r in rows] == ["a", "b"]

        conn.close()


# --- Phase 3: scriptproperties ---


class TestScriptPropertiesExtraction:
    def test_extracts_datatypes(self, tmp_path: Path) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <scriptproperties>
              <datatype name="component" type="">
                <property name="exists" result="true iff exists" type="boolean"/>
                <property name="name" result="the name" type="string"/>
              </datatype>
              <datatype name="ship" type="component">
                <property name="speed" result="current speed" type="length"/>
              </datatype>
            </scriptproperties>
        """)
        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        counts = extract_scriptproperties_to_db(data, conn)
        conn.commit()
        assert counts["datatypes"] == 2
        assert counts["properties"] == 3
        row = conn.execute("SELECT base_type FROM script_datatypes WHERE name = 'ship'").fetchone()
        assert row[0] == "component"
        conn.close()

    def test_extracts_keywords(self, tmp_path: Path) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <scriptproperties>
              <keyword name="player" description="Player data"
                       type="entity" script="any">
                <property name="money" result="player credits" type="money"/>
              </keyword>
              <keyword name="this" description="Current entity" type="component" script="ai"/>
            </scriptproperties>
        """)
        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        counts = extract_scriptproperties_to_db(data, conn)
        conn.commit()
        assert counts["keywords"] == 2
        row = conn.execute("SELECT script FROM script_keywords WHERE name = 'this'").fetchone()
        assert row[0] == "ai"
        conn.close()

    @pytest.mark.skipif(not _HAS_GAME, reason="Game files not available")
    def test_real_scriptproperties(self, tmp_path: Path) -> None:
        from x4_catalog import build_vfs
        from x4_catalog._core import _read_payload

        vfs = build_vfs(_GAME_DIR)
        data = _read_payload(vfs["libraries/scriptproperties.xml"])
        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        counts = extract_scriptproperties_to_db(data, conn)
        conn.commit()
        conn.close()
        assert counts["datatypes"] >= 150
        assert counts["keywords"] >= 80
        assert counts["properties"] >= 1500
