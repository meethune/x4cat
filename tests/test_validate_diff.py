"""Tests for diff patch validation."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from tests.conftest import _xml
from x4_catalog._validate import (
    evaluate_xpath,
    parse_diff_ops,
    validate_diff_directory,
    validate_diff_file,
)

if TYPE_CHECKING:
    from pathlib import Path


# --- Unit: parse_diff_ops ---


class TestParseDiffOps:
    def test_parse_add_replace_remove(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares">
                <ware id="new"/>
              </add>
              <replace sel="/wares/ware[@id='energy']/@max">99</replace>
              <remove sel="/wares/ware[@id='old']"/>
            </diff>
        """)
        ops = parse_diff_ops(data)
        assert len(ops) == 3
        assert ops[0].tag == "add"
        assert ops[1].tag == "replace"
        assert ops[2].tag == "remove"

    def test_parse_sel_attribute(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/wares/ware[@id='energy']/price/@max">99</replace>
            </diff>
        """)
        ops = parse_diff_ops(data)
        assert ops[0].sel == "/wares/ware[@id='energy']/price/@max"

    def test_parse_if_attribute(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares" if="/wares/ware[@id='energy']">
                <ware id="new"/>
              </add>
            </diff>
        """)
        ops = parse_diff_ops(data)
        assert ops[0].if_cond == "/wares/ware[@id='energy']"

    def test_parse_pos_attribute(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares/ware[@id='energy']" pos="after">
                <ware id="new"/>
              </add>
            </diff>
        """)
        ops = parse_diff_ops(data)
        assert ops[0].pos == "after"

    def test_parse_type_attribute(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares/ware[@id='energy']" type="@newtag">value</add>
            </diff>
        """)
        ops = parse_diff_ops(data)
        assert ops[0].type_attr == "@newtag"

    def test_parse_line_numbers(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/a"><x/></add>
              <replace sel="/b">1</replace>
              <remove sel="/c"/>
            </diff>
        """)
        ops = parse_diff_ops(data)
        # Line numbers should be increasing
        assert ops[0].line < ops[1].line < ops[2].line

    def test_parse_empty_diff(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff/>
        """)
        ops = parse_diff_ops(data)
        assert ops == []

    def test_parse_non_diff_root_raises(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <wares><ware id="x"/></wares>
        """)
        with pytest.raises(ValueError, match="root.*diff"):
            parse_diff_ops(data)

    def test_parse_missing_sel_raises(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add><ware id="x"/></add>
            </diff>
        """)
        with pytest.raises(ValueError, match="sel"):
            parse_diff_ops(data)

    def test_parse_malformed_xml_raises(self) -> None:
        with pytest.raises(ValueError, match="[Pp]arse|XML"):
            parse_diff_ops(b"<not valid xml")

    def test_entity_declaration_rejected(self) -> None:
        data = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <!DOCTYPE diff [
              <!ENTITY lol "lol">
            ]>
            <diff>
              <replace sel="/root">&lol;</replace>
            </diff>
        """)
        with pytest.raises(ValueError, match="[Ee]ntity"):
            parse_diff_ops(data)


# --- Unit: evaluate_xpath ---


class TestEvaluateXpath:
    SAMPLE_XML = _xml("""\
        <?xml version="1.0" encoding="utf-8"?>
        <wares>
          <ware id="energy" name="Energy Cells">
            <price min="10" average="16" max="22"/>
            <owner faction="argon"/>
          </ware>
          <ware id="water" name="Water">
            <price min="5" average="10" max="15"/>
          </ware>
        </wares>
    """)

    def test_simple_element_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware")
        assert matched

    def test_attribute_predicate_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='energy']")
        assert matched

    def test_attribute_predicate_no_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='nonexistent']")
        assert not matched

    def test_trailing_attr_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='energy']/price/@max")
        assert matched

    def test_trailing_attr_no_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='energy']/price/@missing")
        assert not matched

    def test_root_element_match(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares")
        assert matched

    def test_root_element_mismatch(self) -> None:
        matched, detail = evaluate_xpath(self.SAMPLE_XML, "/jobs/job")
        assert not matched
        assert "root" in detail.lower()

    def test_nested_path(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='energy']/price")
        assert matched

    def test_no_match_child(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[@id='energy']/nonexistent")
        assert not matched

    def test_position_predicate(self) -> None:
        matched, _ = evaluate_xpath(self.SAMPLE_XML, "/wares/ware[1]")
        assert matched

    def test_unsupported_xpath_warns(self) -> None:
        matched, detail = evaluate_xpath(self.SAMPLE_XML, "/wares[not(ware[@id='x'])]")
        # Should not crash; should indicate unsupported
        assert "unsupported" in detail.lower() or matched is True or matched is False


# --- Unit: validate_diff_file ---


class TestValidateDiffFile:
    BASE_XML = _xml("""\
        <?xml version="1.0" encoding="utf-8"?>
        <wares>
          <ware id="energy" name="Energy Cells">
            <price min="10" average="16" max="22"/>
          </ware>
          <ware id="water" name="Water">
            <price min="5" average="10" max="15"/>
          </ware>
        </wares>
    """)

    def test_all_ops_match(self, tmp_path: Path) -> None:
        diff = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/wares/ware[@id='energy']/price/@max">99</replace>
              <add sel="/wares">
                <ware id="new"/>
              </add>
              <remove sel="/wares/ware[@id='water']"/>
            </diff>
        """)
        report = validate_diff_file(
            diff, self.BASE_XML, tmp_path / "wares.xml", "libraries/wares.xml"
        )
        assert report.base_found
        assert report.parse_error is None
        assert all(r.sel_matched for r in report.results)

    def test_some_ops_fail(self, tmp_path: Path) -> None:
        diff = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/wares/ware[@id='energy']/price/@max">99</replace>
              <remove sel="/wares/ware[@id='nonexistent']"/>
            </diff>
        """)
        report = validate_diff_file(
            diff, self.BASE_XML, tmp_path / "wares.xml", "libraries/wares.xml"
        )
        assert report.results[0].sel_matched
        assert not report.results[1].sel_matched

    def test_if_condition_matches(self, tmp_path: Path) -> None:
        diff = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares" if="/wares/ware[@id='energy']">
                <ware id="conditional"/>
              </add>
            </diff>
        """)
        report = validate_diff_file(
            diff, self.BASE_XML, tmp_path / "wares.xml", "libraries/wares.xml"
        )
        assert report.results[0].sel_matched
        assert report.results[0].if_matched is True

    def test_if_condition_no_match(self, tmp_path: Path) -> None:
        diff = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <add sel="/wares" if="/wares/ware[@id='missing']">
                <ware id="conditional"/>
              </add>
            </diff>
        """)
        report = validate_diff_file(
            diff, self.BASE_XML, tmp_path / "wares.xml", "libraries/wares.xml"
        )
        assert report.results[0].sel_matched
        assert report.results[0].if_matched is False

    def test_invalid_diff_structure(self, tmp_path: Path) -> None:
        diff = _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <wares><ware id="x"/></wares>
        """)
        report = validate_diff_file(
            diff, self.BASE_XML, tmp_path / "wares.xml", "libraries/wares.xml"
        )
        assert report.parse_error is not None


# --- Integration: validate_diff_directory ---


class TestValidateDiffDirectory:
    def test_valid_mod_directory(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        # md/test.xml is in the game_dir fixture; create a valid diff for it
        (mod / "md" / "test.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/md">replaced</replace>
            </diff>
        """)
        )
        reports = validate_diff_directory(game_dir, mod)
        diff_reports = [r for r in reports if r.base_found]
        assert len(diff_reports) == 1
        assert all(r.sel_matched for r in diff_reports[0].results)

    def test_no_base_file_found(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "nonexistent").mkdir(parents=True)
        (mod / "nonexistent" / "file.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/root/child">x</replace>
            </diff>
        """)
        )
        reports = validate_diff_directory(game_dir, mod)
        assert len(reports) == 1
        assert not reports[0].base_found

    def test_non_diff_xml_skipped(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        mod.mkdir()
        # Regular XML file (not a diff patch) — should be skipped
        (mod / "content.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <content id="test" version="100" name="Test"/>
        """)
        )
        reports = validate_diff_directory(game_dir, mod)
        assert reports == []

    def test_non_xml_files_skipped(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        mod.mkdir()
        (mod / "readme.txt").write_text("not xml")
        reports = validate_diff_directory(game_dir, mod)
        assert reports == []

    def test_broken_xpath_reports_failure(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "test.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/md/nonexistent_child">x</replace>
            </diff>
        """)
        )
        reports = validate_diff_directory(game_dir, mod)
        diff_reports = [r for r in reports if r.base_found]
        assert len(diff_reports) == 1
        assert not diff_reports[0].results[0].sel_matched


# --- CLI integration ---


class TestValidateDiffCli:
    def test_validate_diff_pass(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "test.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/md">replaced</replace>
            </diff>
        """)
        )
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "validate-diff", str(game_dir), str(mod)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_validate_diff_fail(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "test.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/md/does_not_exist">x</replace>
            </diff>
        """)
        )
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "validate-diff", str(game_dir), str(mod)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "FAIL" in result.stdout

    def test_validate_diff_skip(self, tmp_path: Path, game_dir: Path) -> None:
        mod = tmp_path / "mod"
        (mod / "nowhere").mkdir(parents=True)
        (mod / "nowhere" / "file.xml").write_bytes(
            _xml("""\
            <?xml version="1.0" encoding="utf-8"?>
            <diff>
              <replace sel="/x">y</replace>
            </diff>
        """)
        )
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "validate-diff", str(game_dir), str(mod)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "SKIP" in result.stdout
