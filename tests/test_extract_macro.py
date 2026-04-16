"""Tests for x4cat extract-macro."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from tests.conftest import make_indexed_game_dir
from x4_catalog._extract_macro import extract_macro
from x4_catalog._index import build_index

if TYPE_CHECKING:
    from pathlib import Path


class TestExtractMacro:
    def test_extract_by_id(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
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
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        extract_macro("ship_test_macro", db, game, out)
        expected = out / "assets" / "units" / "size_s" / "macros" / "ship_test_macro.xml"
        assert expected.exists()

    def test_extract_nonexistent_returns_none(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "output"
        result = extract_macro("nonexistent_macro", db, game, out)
        assert result is None

    def test_extract_creates_output_dir(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        out = tmp_path / "nested" / "output"
        result = extract_macro("ship_test_macro", db, game, out)
        assert result is not None
        assert out.is_dir()


class TestExtractMacroCli:
    def test_extract_macro_subcommand(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
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
        game, _ = make_indexed_game_dir(tmp_path)
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
        game, _ = make_indexed_game_dir(tmp_path)
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


class TestExtractMacroPathTraversal:
    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        """A macro with a traversal path should be rejected."""
        import sqlite3

        # Create a DB with a malicious macro path
        db = tmp_path / "evil.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE macros (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute(
            "INSERT INTO macros VALUES (?, ?)",
            ("evil_macro", "../../etc/cron.d/evil"),
        )
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("INSERT INTO meta VALUES ('game_dir', ?)", (str(tmp_path),))
        conn.commit()
        conn.close()

        # Create a fake game dir with matching VFS entry
        from tests.conftest import _write_cat_dat

        _write_cat_dat(
            tmp_path,
            "01.cat",
            [("../../etc/cron.d/evil.xml", b"<pwned/>", 1000000)],
        )

        out = tmp_path / "output"
        import pytest

        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            extract_macro("evil_macro", db, tmp_path, out)
