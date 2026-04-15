"""Tests for mod conflict detection."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from typing import TYPE_CHECKING

from x4_catalog._conflicts import check_conflicts

if TYPE_CHECKING:
    from pathlib import Path


def _xml(text: str) -> bytes:
    return textwrap.dedent(text).strip().encode()


def _make_mod(tmp_path: Path, name: str, files: dict[str, bytes]) -> Path:
    mod = tmp_path / name
    for rel_path, content in files.items():
        p = mod / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    return mod


# --- Conflict classification ---


class TestCheckConflicts:
    def test_no_overlap_clean(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="a"/></add>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/jobs.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/jobs"><job id="b"/></add>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert result["conflicts"] == []
        assert result["safe"] == []

    def test_add_add_same_parent_is_safe(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="a"/></add>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="b"/></add>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert result["conflicts"] == []
        assert len(result["safe"]) >= 1

    def test_replace_replace_same_sel_is_conflict(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='energy']/price/@max">99</replace>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='energy']/price/@max">50</replace>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert len(result["conflicts"]) >= 1
        c = result["conflicts"][0]
        assert "mod_a" in c["mods"]
        assert "mod_b" in c["mods"]
        assert "energy" in c["sel"]

    def test_remove_vs_replace_is_conflict(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <remove sel="/wares/ware[@id='energy']"/>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='energy']/@name">New</replace>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert len(result["conflicts"]) >= 1

    def test_three_mods(self, tmp_path: Path) -> None:
        common_file = "libraries/gamestarts.xml"
        mods = []
        for name in ["mod_a", "mod_b", "mod_c"]:
            mods.append(
                _make_mod(
                    tmp_path,
                    name,
                    {
                        common_file: _xml(f"""\
                    <?xml version="1.0" encoding="utf-8"?>
                    <diff>
                      <replace sel="/gamestarts/gamestart[@id='tut1']/@name">
                        {name}
                      </replace>
                    </diff>
                """),
                    },
                )
            )
        result = check_conflicts(mods)
        assert len(result["conflicts"]) >= 1
        assert len(result["conflicts"][0]["mods"]) == 3

    def test_non_diff_files_skipped(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "content.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <content id="a" version="100" name="A"/>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "content.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <content id="b" version="100" name="B"/>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert result["conflicts"] == []

    def test_mixed_add_replace_is_info(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares/ware[@id='energy']">
                    <production method="custom"/>
                  </add>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='energy']/@name">X</replace>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        # Different sels — no overlap
        assert result["conflicts"] == []

    def test_result_has_file_path(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='x']/@v">1</replace>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='x']/@v">2</replace>
                </diff>
            """),
            },
        )
        result = check_conflicts([mod_a, mod_b])
        assert result["conflicts"][0]["file"] == "libraries/wares.xml"


# --- CLI ---


class TestConflictsCli:
    def test_check_conflicts_clean(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="a"/></add>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/jobs.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/jobs"><job id="b"/></add>
                </diff>
            """),
            },
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "check-conflicts",
                str(mod_a),
                str(mod_b),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_check_conflicts_detected(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='x']/@v">1</replace>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <replace sel="/wares/ware[@id='x']/@v">2</replace>
                </diff>
            """),
            },
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "check-conflicts",
                str(mod_a),
                str(mod_b),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "CONFLICT" in result.stdout

    def test_verbose_shows_safe(self, tmp_path: Path) -> None:
        mod_a = _make_mod(
            tmp_path,
            "mod_a",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="a"/></add>
                </diff>
            """),
            },
        )
        mod_b = _make_mod(
            tmp_path,
            "mod_b",
            {
                "libraries/wares.xml": _xml("""\
                <?xml version="1.0" encoding="utf-8"?>
                <diff>
                  <add sel="/wares"><ware id="b"/></add>
                </diff>
            """),
            },
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "check-conflicts",
                str(mod_a),
                str(mod_b),
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "SAFE" in result.stdout
