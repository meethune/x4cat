"""Tests for x4_catalog — the XRCatTool-equivalent CLI."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from tests.conftest import _md5
from x4_catalog import (
    build_vfs,
    build_vfs_multi,
    diff_file_sets,
    extract_to_disk,
    iter_cat_files,
    list_entries,
    pack_catalog,
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

    def test_subst_prefix(self, game_dir: Path) -> None:
        (game_dir / "subst_01.cat").write_text(f"md/subst.xml 5 100 {_md5(b'hello')}\n")
        (game_dir / "subst_01.dat").write_bytes(b"hello")
        cats = iter_cat_files(game_dir, prefix="subst_")
        assert len(cats) == 1
        assert cats[0].name == "subst_01.cat"


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


# --- Unit: build_vfs_multi ---


class TestBuildVfsMulti:
    def test_single_source(self, game_dir: Path) -> None:
        vfs = build_vfs_multi([(game_dir, "")])
        assert len(vfs) == 3

    def test_later_source_overrides(self, game_dir: Path, ext_dir: Path) -> None:
        vfs = build_vfs_multi([(game_dir, ""), (ext_dir, "ext_")])
        # ext overwrites libraries/wares.xml and adds md/dlc_mission.xml
        assert len(vfs) == 4
        wares_entry = vfs["libraries/wares.xml"]
        assert wares_entry.cat_path.name == "ext_01.cat"

    def test_three_sources(self, game_dir: Path, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        third = tmp_path / "third"
        third.mkdir()
        _write_cat_dat(
            third,
            "01.cat",
            [("md/test.xml", b"<md>third</md>", 9000000)],
        )
        vfs = build_vfs_multi([(game_dir, ""), (third, "")])
        assert vfs["md/test.xml"].cat_path.parent == third


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

    def test_include_regex(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, include_re=r"^aiscripts/")
        assert len(entries) == 1
        assert entries[0].path == "aiscripts/order.trade.xml"

    def test_exclude_regex(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, exclude_re=r"^md/")
        paths = {e.path for e in entries}
        assert "md/test.xml" not in paths
        assert "libraries/wares.xml" in paths
        assert "aiscripts/order.trade.xml" in paths

    def test_include_and_exclude_combined(self, game_dir: Path) -> None:
        entries = list_entries(game_dir, include_re=r"\.xml$", exclude_re=r"^aiscripts/")
        paths = {e.path for e in entries}
        assert "aiscripts/order.trade.xml" not in paths
        assert "md/test.xml" in paths


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

    def test_extract_preserves_mtime(self, game_dir: Path, tmp_path: Path) -> None:
        out = tmp_path / "output"
        extract_to_disk(game_dir, out, glob_pattern="libraries/wares.xml")
        dest = out / "libraries" / "wares.xml"
        assert int(dest.stat().st_mtime) == 1000001


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


# --- Integration: pack_catalog ---


class TestPackCatalog:
    def test_pack_from_loose_files(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        (src / "md").mkdir(parents=True)
        (src / "md" / "hello.xml").write_bytes(b"<hello/>")
        (src / "md" / "world.xml").write_bytes(b"<world/>")

        cat_path = tmp_path / "out" / "ext_01.cat"
        pack_catalog(src, cat_path)

        assert cat_path.exists()
        assert cat_path.with_suffix(".dat").exists()

        # verify round-trip: read back with build_vfs
        vfs = build_vfs(cat_path.parent, prefix="ext_")
        assert set(vfs.keys()) == {"md/hello.xml", "md/world.xml"}

    def test_pack_content_matches(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "data.txt").write_bytes(b"test content")

        cat_path = tmp_path / "01.cat"
        pack_catalog(src, cat_path)

        vfs = build_vfs(tmp_path)
        from x4_catalog._core import read_payload

        data = read_payload(vfs["data.txt"])
        assert data == b"test content"

    def test_pack_md5_correct(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        content = b"check my hash"
        (src / "file.bin").write_bytes(content)

        cat_path = tmp_path / "01.cat"
        pack_catalog(src, cat_path)

        vfs = build_vfs(tmp_path)
        assert vfs["file.bin"].md5 == _md5(content)

    def test_pack_empty_dir_creates_empty_catalog(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()

        cat_path = tmp_path / "01.cat"
        pack_catalog(src, cat_path)

        assert cat_path.read_text() == ""
        assert cat_path.with_suffix(".dat").read_bytes() == b""

    def test_pack_preserves_subdirectory_structure(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        (src / "a" / "b" / "c").mkdir(parents=True)
        (src / "a" / "b" / "c" / "deep.xml").write_bytes(b"<deep/>")

        cat_path = tmp_path / "01.cat"
        pack_catalog(src, cat_path)

        vfs = build_vfs(tmp_path)
        assert "a/b/c/deep.xml" in vfs


# --- Integration: pack_catalog append ---


class TestPackCatalogAppend:
    def test_append_adds_entries(self, tmp_path: Path) -> None:
        # first pack
        src1 = tmp_path / "src1"
        src1.mkdir()
        (src1 / "a.txt").write_bytes(b"aaa")
        cat_path = tmp_path / "01.cat"
        pack_catalog(src1, cat_path)

        # append second batch
        src2 = tmp_path / "src2"
        src2.mkdir()
        (src2 / "b.txt").write_bytes(b"bbb")
        pack_catalog(src2, cat_path, append=True)

        vfs = build_vfs(tmp_path)
        assert "a.txt" in vfs
        assert "b.txt" in vfs

    def test_append_overrides_existing_path(self, tmp_path: Path) -> None:
        src1 = tmp_path / "src1"
        src1.mkdir()
        (src1 / "file.txt").write_bytes(b"original")
        cat_path = tmp_path / "01.cat"
        pack_catalog(src1, cat_path)

        src2 = tmp_path / "src2"
        src2.mkdir()
        (src2 / "file.txt").write_bytes(b"appended")
        pack_catalog(src2, cat_path, append=True)

        # both entries exist in .cat but build_vfs takes the last one
        vfs = build_vfs(tmp_path)
        from x4_catalog._core import read_payload

        data = read_payload(vfs["file.txt"])
        assert data == b"appended"


# --- Integration: diff_file_sets ---


class TestDiffFileSets:
    def test_new_file_included(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        (base / "md").mkdir(parents=True)
        (base / "md" / "old.xml").write_bytes(b"<old/>")

        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "old.xml").write_bytes(b"<old/>")
        (mod / "md" / "new.xml").write_bytes(b"<new/>")

        changed, deleted = diff_file_sets(base, mod)
        assert "md/new.xml" in changed
        assert deleted == []

    def test_changed_file_included(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        (base / "md").mkdir(parents=True)
        (base / "md" / "script.xml").write_bytes(b"<original/>")

        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "script.xml").write_bytes(b"<modified/>")

        changed, deleted = diff_file_sets(base, mod)
        assert "md/script.xml" in changed
        assert deleted == []

    def test_identical_file_excluded(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        (base / "same.xml").write_bytes(b"<same/>")

        mod = tmp_path / "mod"
        mod.mkdir()
        (mod / "same.xml").write_bytes(b"<same/>")

        changed, deleted = diff_file_sets(base, mod)
        assert changed == {}
        assert deleted == []

    def test_deleted_file_tracked(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        (base / "md").mkdir(parents=True)
        (base / "md" / "removed.xml").write_bytes(b"<gone/>")
        (base / "md" / "kept.xml").write_bytes(b"<here/>")

        mod = tmp_path / "mod"
        (mod / "md").mkdir(parents=True)
        (mod / "md" / "kept.xml").write_bytes(b"<here/>")

        changed, deleted = diff_file_sets(base, mod)
        assert "md/removed.xml" in deleted
        assert changed == {}

    def test_diff_combined_scenario(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        (base / "a").mkdir(parents=True)
        (base / "a" / "same.xml").write_bytes(b"<same/>")
        (base / "a" / "changed.xml").write_bytes(b"<v1/>")
        (base / "a" / "removed.xml").write_bytes(b"<bye/>")

        mod = tmp_path / "mod"
        (mod / "a").mkdir(parents=True)
        (mod / "a" / "same.xml").write_bytes(b"<same/>")
        (mod / "a" / "changed.xml").write_bytes(b"<v2/>")
        (mod / "a" / "added.xml").write_bytes(b"<new/>")

        changed, deleted = diff_file_sets(base, mod)
        assert set(changed.keys()) == {"a/changed.xml", "a/added.xml"}
        assert deleted == ["a/removed.xml"]

    def test_diff_from_catalogs(self, game_dir: Path, tmp_path: Path) -> None:
        # extract base game to a directory
        base_dir = tmp_path / "base_extracted"
        extract_to_disk(game_dir, base_dir)

        # make a modification
        mod_dir = tmp_path / "mod_extracted"
        extract_to_disk(game_dir, mod_dir)
        (mod_dir / "md" / "test.xml").write_bytes(b"<md>modded</md>")
        (mod_dir / "md" / "brand_new.xml").write_bytes(b"<new/>")

        changed, deleted = diff_file_sets(base_dir, mod_dir)
        assert "md/test.xml" in changed
        assert "md/brand_new.xml" in changed
        assert "libraries/wares.xml" not in changed
        assert deleted == []


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

    def test_list_with_include_regex(self, game_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "x4_catalog", "list", str(game_dir), "--include", "^md/"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "md/test.xml" in result.stdout
        assert "wares.xml" not in result.stdout

    def test_list_with_exclude_regex(self, game_dir: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "list",
                str(game_dir),
                "--exclude",
                "^(md|aiscripts)/",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "wares.xml" in result.stdout
        assert "test.xml" not in result.stdout

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

    def test_pack_subcommand(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "test.txt").write_bytes(b"packed")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "pack",
                str(src),
                "-o",
                str(tmp_path / "ext_01.cat"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (tmp_path / "ext_01.cat").exists()
        assert (tmp_path / "ext_01.dat").exists()

    def test_pack_append_subcommand(self, tmp_path: Path) -> None:
        src1 = tmp_path / "src1"
        src1.mkdir()
        (src1 / "a.txt").write_bytes(b"aaa")

        cat = tmp_path / "01.cat"
        subprocess.run(
            [sys.executable, "-m", "x4_catalog", "pack", str(src1), "-o", str(cat)],
            capture_output=True,
            check=True,
        )

        src2 = tmp_path / "src2"
        src2.mkdir()
        (src2 / "b.txt").write_bytes(b"bbb")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "pack",
                str(src2),
                "-o",
                str(cat),
                "--append",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_diff_subcommand(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        (base / "same.xml").write_bytes(b"<same/>")
        (base / "old.xml").write_bytes(b"<old/>")

        mod = tmp_path / "mod"
        mod.mkdir()
        (mod / "same.xml").write_bytes(b"<same/>")
        (mod / "old.xml").write_bytes(b"<changed/>")
        (mod / "new.xml").write_bytes(b"<new/>")

        out_cat = tmp_path / "diff" / "ext_01.cat"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "diff",
                "--base",
                str(base),
                "--mod",
                str(mod),
                "-o",
                str(out_cat),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert out_cat.exists()

        # the diff catalog should contain only old.xml (changed) and new.xml (added)
        vfs = build_vfs(out_cat.parent, prefix="ext_")
        assert set(vfs.keys()) == {"old.xml", "new.xml"}


# --- Security: path traversal ---


class TestPathTraversal:
    def test_dotdot_path_rejected_on_extract(self, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        _write_cat_dat(
            tmp_path,
            "01.cat",
            [("../../etc/evil.txt", b"pwned", 1000000)],
        )
        out = tmp_path / "output"
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            extract_to_disk(tmp_path, out)

    def test_absolute_path_stripped_to_relative(self, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        _write_cat_dat(
            tmp_path,
            "01.cat",
            [("/etc/passwd", b"root:x:0:0", 1000000)],
        )
        out = tmp_path / "output"
        # leading / is stripped by parse_cat_line, so it extracts safely as etc/passwd
        result = extract_to_disk(tmp_path, out)
        assert len(result) == 1
        assert (out / "etc" / "passwd").exists()

    def test_sneaky_dotdot_in_middle_rejected(self, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        _write_cat_dat(
            tmp_path,
            "01.cat",
            [("md/../../../etc/shadow", b"nope", 1000000)],
        )
        out = tmp_path / "output"
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            extract_to_disk(tmp_path, out)

    def test_safe_path_still_works(self, tmp_path: Path) -> None:
        from tests.conftest import _write_cat_dat

        _write_cat_dat(
            tmp_path,
            "01.cat",
            [("md/safe_script.xml", b"<safe/>", 1000000)],
        )
        out = tmp_path / "output"
        result = extract_to_disk(tmp_path, out)
        assert len(result) == 1
        assert (out / "md" / "safe_script.xml").read_bytes() == b"<safe/>"


# --- Security: input validation ---


class TestInputValidation:
    def test_negative_size_rejected(self) -> None:
        with pytest.raises(ValueError, match="[Nn]egative size"):
            parse_cat_line("file.xml -1 1000 abcdef1234567890abcdef1234567890")

    def test_negative_mtime_rejected(self) -> None:
        with pytest.raises(ValueError, match="[Nn]egative mtime"):
            parse_cat_line("file.xml 10 -1 abcdef1234567890abcdef1234567890")

    def test_invalid_md5_rejected(self) -> None:
        with pytest.raises(ValueError, match="[Ii]nvalid MD5"):
            parse_cat_line("file.xml 10 1000 not-a-hash")

    def test_too_few_fields_rejected(self) -> None:
        with pytest.raises(ValueError, match="[Mm]alformed"):
            parse_cat_line("onlytwo fields")

    def test_trailing_spaces_handled(self) -> None:
        entry = parse_cat_line("file.xml 10 1000 abcdef1234567890abcdef1234567890   ")
        assert entry.path == "file.xml"
        assert entry.md5 == "abcdef1234567890abcdef1234567890"

    def test_malformed_lines_skipped_in_index(self, tmp_path: Path) -> None:
        (tmp_path / "01.cat").write_text(
            "good.xml 4 1000 d3b07384d113edec49eaa6238ad5ff00\n"
            "bad line\n"
            "also_bad -1 1000 abcdef1234567890abcdef1234567890\n",
            encoding="utf-8",
        )
        (tmp_path / "01.dat").write_bytes(b"good")
        vfs = build_vfs(tmp_path)
        assert list(vfs.keys()) == ["good.xml"]


# --- Security: symlink safety ---


class TestSymlinkSafety:
    def test_symlinks_skipped_in_pack(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        src.mkdir()
        (src / "real.txt").write_bytes(b"real")
        (src / "link.txt").symlink_to(src / "real.txt")

        cat_path = tmp_path / "01.cat"
        count = pack_catalog(src, cat_path)
        assert count == 1  # only real.txt, not the symlink

        vfs = build_vfs(tmp_path)
        assert "real.txt" in vfs
        assert "link.txt" not in vfs

    def test_symlinks_skipped_in_diff(self, tmp_path: Path) -> None:
        base = tmp_path / "base"
        base.mkdir()
        (base / "file.txt").write_bytes(b"hello")

        mod = tmp_path / "mod"
        mod.mkdir()
        (mod / "file.txt").write_bytes(b"hello")
        (mod / "sneaky.txt").symlink_to("/etc/hostname")

        changed, _deleted = diff_file_sets(base, mod)
        # symlink should not appear in changed set
        assert "sneaky.txt" not in changed


# --- Security: MD5 integrity verification ---


class TestMd5Verification:
    def test_corrupted_dat_detected(self, tmp_path: Path) -> None:
        from x4_catalog._core import read_payload

        # write valid cat but corrupt the dat
        (tmp_path / "01.cat").write_text(
            f"file.txt 5 1000 {_md5(b'hello')}\n",
            encoding="utf-8",
        )
        (tmp_path / "01.dat").write_bytes(b"wrong")

        vfs = build_vfs(tmp_path)
        with pytest.raises(OSError, match="MD5 mismatch"):
            read_payload(vfs["file.txt"])
