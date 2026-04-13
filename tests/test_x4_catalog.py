"""Tests for x4_catalog — the XRCatTool-equivalent CLI."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from x4_catalog import (
    build_vfs,
    extract_to_disk,
    iter_cat_files,
    list_entries,
    parse_cat_line,
)

if TYPE_CHECKING:
    from pathlib import Path


# --- Unit: parse_cat_line ---


class TestParseCatLine:
    def test_simple_path(self) -> None:
        entry = parse_cat_line("md/test.xml 123 999999 abcdef1234567890abcdef1234567890")
        assert entry.path == "md/test.xml"
        assert entry.size == 123
        assert entry.mtime == 999999
        assert entry.md5 == "abcdef1234567890abcdef1234567890"

    def test_path_with_spaces(self) -> None:
        line = "assets/some folder/file.xmf 456 888888 00112233445566778899aabbccddeeff"
        entry = parse_cat_line(line)
        assert entry.path == "assets/some folder/file.xmf"
        assert entry.size == 456

    def test_backslash_normalized(self) -> None:
        entry = parse_cat_line("md\\test.xml 10 100 abcdef1234567890abcdef1234567890")
        assert entry.path == "md/test.xml"

    def test_empty_line_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_cat_line("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            parse_cat_line("   \n")


# --- Unit: iter_cat_files ---


class TestIterCatFiles:
    def test_returns_sorted_numeric_cats(self, game_dir: Path) -> None:
        cats = iter_cat_files(game_dir)
        names = [c.name for c in cats]
        assert names == ["01.cat", "02.cat"]

    def test_skips_sig_cats(self, game_dir: Path) -> None:
        (game_dir / "01_sig.cat").write_text("sig data\n")
        cats = iter_cat_files(game_dir)
        assert all("sig" not in c.name for c in cats)

    def test_skips_ext_cats(self, game_dir: Path) -> None:
        (game_dir / "ext_01.cat").write_text("ext data\n")
        cats = iter_cat_files(game_dir)
        assert all("ext" not in c.name for c in cats)


# --- Unit: build_vfs ---


class TestBuildVfs:
    def test_later_catalog_overrides(self, game_dir: Path) -> None:
        vfs = build_vfs(game_dir)
        entry = vfs["md/test.xml"]
        # 02.cat should override 01.cat
        assert entry.cat_path.name == "02.cat"

    def test_all_unique_paths_present(self, game_dir: Path) -> None:
        vfs = build_vfs(game_dir)
        assert set(vfs.keys()) == {
            "md/test.xml",
            "libraries/wares.xml",
            "aiscripts/order.trade.xml",
        }


# --- Unit: list_entries ---


class TestListEntries:
    def test_no_filter_returns_all(self, game_dir: Path) -> None:
        entries = list_entries(game_dir)
        assert len(entries) == 3

    def test_glob_filter(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, glob_pattern="md/*")
        assert len(entries) == 1
        assert entries[0].path == "md/test.xml"

    def test_glob_filter_recursive(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, glob_pattern="**/*.xml")
        assert len(entries) == 3

    def test_glob_filter_no_match(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, glob_pattern="nonexistent/*")
        assert entries == []


# --- Integration: extract_to_disk ---


class TestExtractToDisk:
    def test_extract_single_file(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extracted = extract_to_disk(game_dir, out, glob_pattern="libraries/wares.xml")
        assert len(extracted) == 1
        content = (out / "libraries" / "wares.xml").read_bytes()
        assert content == b"<wares/>"

    def test_extract_overridden_file_gets_latest(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extract_to_disk(game_dir, out, glob_pattern="md/test.xml")
        content = (out / "md" / "test.xml").read_bytes()
        assert content == b"<md>updated</md>"

    def test_extract_all(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extracted = extract_to_disk(game_dir, out)
        assert len(extracted) == 3
        assert (out / "aiscripts" / "order.trade.xml").exists()

    def test_extract_preserves_directory_structure(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extract_to_disk(game_dir, out, glob_pattern="aiscripts/*")
        assert (out / "aiscripts" / "order.trade.xml").is_file()

    def test_extract_no_match_returns_empty(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extracted = extract_to_disk(game_dir, out, glob_pattern="nope/*")
        assert extracted == []
        assert not out.exists()


# --- Integration: extension catalogs ---


class TestExtensionCatalogs:
    def test_ext_cat_files_found(self, ext_dir: Path) -> None:
        cats = iter_cat_files(ext_dir, prefix="ext_")
        assert len(cats) == 1
        assert cats[0].name == "ext_01.cat"

    def test_ext_extract(self, ext_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extracted = extract_to_disk(ext_dir, out, prefix="ext_")
        assert len(extracted) == 2
        content = (out / "md" / "dlc_mission.xml").read_bytes()
        assert content == b"<md>dlc</md>"


# --- CLI integration ---


class TestCli:
    def test_list_subcommand(self, game_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "list", str(game_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "md/test.xml" in result.stdout

    def test_list_with_glob(self, game_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "list", str(game_dir), "-g", "aiscripts/*"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "order.trade.xml" in result.stdout
        assert "wares.xml" not in result.stdout

    def test_extract_subcommand(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "extracted"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "extract",
                str(game_dir),
                "-o",
                str(out),
                "-g",
                "md/*",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "md" / "test.xml").is_file()

    def test_extract_no_output_dir_errors(self, game_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "extract", str(game_dir)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
