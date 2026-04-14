"""Tests for XML diff patch generation."""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from tests.conftest import _xml
from x4_catalog._xmldiff import generate_diff

if TYPE_CHECKING:
    from pathlib import Path


def _diff_ops(diff_bytes: bytes) -> list[ET.Element]:
    """Parse diff XML and return the list of operation elements."""
    root = ET.fromstring(diff_bytes)
    assert root.tag == "diff"
    return list(root)


# --- Attribute changes ---


class TestAttributeChanges:
    def test_replace_attribute_value(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="22"/>
              </ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="99"/>
              </ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "replace"
        assert "@max" in ops[0].attrib["sel"]
        assert ops[0].text == "99"

    def test_add_new_attribute(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10"/>
              </ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="99"/>
              </ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "add"
        assert ops[0].attrib.get("type") == "@max"
        assert ops[0].text == "99"

    def test_remove_attribute(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="22"/>
              </ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10"/>
              </ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "remove"
        assert "@max" in ops[0].attrib["sel"]


# --- Element changes ---


class TestElementChanges:
    def test_add_new_child_element(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10"/>
              </ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10"/>
              </ware>
              <ware id="water">
                <price min="5"/>
              </ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "add"
        added = ops[0].find("ware")
        assert added is not None
        assert added.get("id") == "water"

    def test_remove_child_element(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy"><price min="10"/></ware>
              <ware id="water"><price min="5"/></ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy"><price min="10"/></ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "remove"
        assert "water" in ops[0].attrib["sel"]

    def test_add_element_to_empty_parent(self) -> None:
        base = _xml("<wares/>")
        mod = _xml("""\
            <wares>
              <ware id="new"><price min="1"/></ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "add"


# --- Text content changes ---


class TestTextChanges:
    def test_replace_text_content(self) -> None:
        base = _xml("""\
            <root>
              <item id="a">old text</item>
            </root>
        """)
        mod = _xml("""\
            <root>
              <item id="a">new text</item>
            </root>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        assert ops[0].tag == "replace"

    def test_add_text_where_none_existed(self) -> None:
        base = _xml("""\
            <root>
              <item id="a"/>
            </root>
        """)
        mod = _xml("""\
            <root>
              <item id="a">new text</item>
            </root>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) >= 1


# --- XPath selector quality ---


class TestXpathSelectors:
    def test_uses_id_attribute_in_selector(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy"><price min="10"/></ware>
              <ware id="water"><price min="5"/></ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy"><price min="10"/></ware>
              <ware id="water"><price min="99"/></ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) == 1
        sel = ops[0].attrib["sel"]
        assert "[@id='water']" in sel

    def test_uses_name_attribute_when_no_id(self) -> None:
        base = _xml("""\
            <scripts>
              <script name="MyScript"><cue value="1"/></script>
            </scripts>
        """)
        mod = _xml("""\
            <scripts>
              <script name="MyScript"><cue value="2"/></script>
            </scripts>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        sel = ops[0].attrib["sel"]
        assert "[@name='MyScript']" in sel

    def test_falls_back_to_position_when_no_id_or_name(self) -> None:
        base = _xml("""\
            <root>
              <item>a</item>
              <item>b</item>
            </root>
        """)
        mod = _xml("""\
            <root>
              <item>a</item>
              <item>changed</item>
            </root>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        assert len(ops) >= 1


# --- No changes ---


class TestNoChanges:
    def test_identical_files_produce_empty_diff(self) -> None:
        xml = _xml("""\
            <wares>
              <ware id="energy"><price min="10"/></ware>
            </wares>
        """)
        result = generate_diff(xml, xml)
        ops = _diff_ops(result)
        assert ops == []


# --- Combined scenarios ---


class TestCombinedScenarios:
    def test_multiple_changes(self) -> None:
        base = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="22"/>
              </ware>
              <ware id="water">
                <price min="5" max="15"/>
              </ware>
            </wares>
        """)
        mod = _xml("""\
            <wares>
              <ware id="energy">
                <price min="10" max="99"/>
              </ware>
              <ware id="food">
                <price min="20" max="40"/>
              </ware>
            </wares>
        """)
        result = generate_diff(base, mod)
        ops = _diff_ops(result)
        tags = {op.tag for op in ops}
        assert "replace" in tags  # energy max changed
        assert "add" in tags  # food added
        assert "remove" in tags  # water removed

    def test_output_is_valid_xml(self) -> None:
        base = _xml("<root><a id='x'>text</a></root>")
        mod = _xml("<root><a id='x'>changed</a><b id='y'/></root>")
        result = generate_diff(base, mod)
        # Should parse without error
        root = ET.fromstring(result)
        assert root.tag == "diff"


# --- CLI integration ---


class TestXmldiffCli:
    def test_xmldiff_stdout(self, tmp_path: Path) -> None:
        base = tmp_path / "base.xml"
        mod = tmp_path / "mod.xml"
        base.write_bytes(
            _xml("""\
            <wares>
              <ware id="energy"><price min="10" max="22"/></ware>
            </wares>
        """)
        )
        mod.write_bytes(
            _xml("""\
            <wares>
              <ware id="energy"><price min="10" max="99"/></ware>
            </wares>
        """)
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "xmldiff",
                "--base",
                str(base),
                "--mod",
                str(mod),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "<diff>" in result.stdout
        assert "<replace" in result.stdout

    def test_xmldiff_output_file(self, tmp_path: Path) -> None:
        base = tmp_path / "base.xml"
        mod = tmp_path / "mod.xml"
        out = tmp_path / "patch.xml"
        base.write_bytes(_xml("<root><a id='x'/></root>"))
        mod.write_bytes(_xml("<root><a id='x'/><b id='y'/></root>"))
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "xmldiff",
                "--base",
                str(base),
                "--mod",
                str(mod),
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out.exists()
        root = ET.parse(out).getroot()
        assert root.tag == "diff"

    def test_xmldiff_no_changes(self, tmp_path: Path) -> None:
        f = tmp_path / "same.xml"
        f.write_bytes(_xml("<root><a/></root>"))
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "xmldiff", "--base", str(f), "--mod", str(f)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "<diff" in result.stdout
