"""Tests for x4cat inspect."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from tests.conftest import make_indexed_game_dir
from x4_catalog._index import build_index
from x4_catalog._inspect import inspect_asset

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def indexed_game(tmp_path: Path) -> tuple[Path, Path]:
    """Build a game dir and index it. Returns (game_dir, db_path)."""
    game, _ = make_indexed_game_dir(tmp_path)
    db = tmp_path / "test.db"
    build_index(game, db)
    return game, db


class TestInspectAsset:
    def test_inspect_ware_by_id(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("energycells", db)
        assert result is not None
        assert result["ware_id"] == "energycells"
        assert result["price_avg"] == 16
        assert "argon" in result["owners"]
        assert "teladi" in result["owners"]

    def test_inspect_macro_by_id(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        assert result["macro_name"] == "ship_test_macro"
        assert "assets/units/size_s/macros/ship_test_macro" in result["macro_path"]

    def test_inspect_shows_component_ref(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        assert result.get("component_ref") == "ship_test"

    def test_inspect_shows_macro_properties(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("ship_test_macro", db)
        assert result is not None
        props = result.get("properties", {})
        assert props.get("hull.max") == "3100"
        assert props.get("ship.type") == "fighter"

    def test_inspect_ware_shows_macro_link(self, indexed_game: tuple[Path, Path]) -> None:
        result = inspect_asset("ship_test", indexed_game[1])
        assert result is not None
        assert result["ware_id"] == "ship_test"
        # Should find the linked macro
        assert result.get("macro_name") == "ship_test_macro"

    def test_inspect_nonexistent_returns_none(self, indexed_game: tuple[Path, Path]) -> None:
        _, db = indexed_game
        result = inspect_asset("nonexistent_thing", db)
        assert result is None


class TestInspectCli:
    def test_inspect_subcommand(self, tmp_path: Path) -> None:
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
                "inspect",
                "energycells",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "energycells" in result.stdout
        assert "16" in result.stdout  # price_avg

    def test_inspect_macro(self, tmp_path: Path) -> None:
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
                "inspect",
                "ship_test_macro",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "ship_test_macro" in result.stdout
        assert "3100" in result.stdout  # hull

    def test_inspect_not_found(self, tmp_path: Path) -> None:
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
                "inspect",
                "nonexistent",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_inspect_no_index_errors(self, tmp_path: Path) -> None:
        db = tmp_path / "nonexistent.db"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "inspect",
                "energycells",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()
