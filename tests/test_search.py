"""Tests for x4cat search."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from tests.conftest import make_indexed_game_dir
from x4_catalog._index import build_index
from x4_catalog._search import search_assets

if TYPE_CHECKING:
    from pathlib import Path


class TestSearchAssets:
    def test_search_by_partial_id(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db)
        ids = {r["id"] for r in results}
        assert "ship_test_s_fighter_01_a_macro" in ids
        assert "ship_test_s_fighter_01_a" in ids  # ware
        assert "ship_test_s_fighter_01" in ids  # component

    def test_search_no_match(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("nonexistent_xyz", db)
        assert results == []

    def test_search_by_group(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("hightech", db)
        ids = {r["id"] for r in results}
        assert "advancedcomposites" in ids

    def test_search_by_tag(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("economy", db)
        ids = {r["id"] for r in results}
        assert "energycells" in ids

    def test_search_case_insensitive(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results_lower = search_assets("fighter", db)
        results_upper = search_assets("FIGHTER", db)
        assert len(results_lower) == len(results_upper)

    def test_search_results_have_type(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db)
        types = {r["type"] for r in results}
        assert "macro" in types
        assert "ware" in types
        assert "component" in types

    def test_search_results_have_path(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("weapon", db)
        macro_results = [r for r in results if r["type"] == "macro"]
        assert macro_results
        assert macro_results[0]["path"]

    def test_search_type_filter(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
        db = tmp_path / "test.db"
        build_index(game, db)
        results = search_assets("fighter", db, type_filter="ware")
        assert all(r["type"] == "ware" for r in results)
        assert len(results) >= 1


class TestSearchCli:
    def test_search_subcommand(self, tmp_path: Path) -> None:
        game, _ = make_indexed_game_dir(tmp_path)
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
        game, _ = make_indexed_game_dir(tmp_path)
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
