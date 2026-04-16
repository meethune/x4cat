"""Tests for x4cat scaffold."""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from tests.conftest import make_indexed_game_dir
from x4_catalog._scaffold import scaffold_equipment, scaffold_ship, scaffold_ware

if TYPE_CHECKING:
    from pathlib import Path


class TestScaffoldWare:
    def test_generates_wares_diff(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        wares = out / "libraries" / "wares.xml"
        assert wares.exists()
        root = ET.parse(wares).getroot()
        assert root.tag == "diff"

    def test_wares_diff_has_correct_id(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        root = ET.parse(out / "libraries" / "wares.xml").getroot()
        add = root.find("add")
        assert add is not None
        ware = add.find("ware")
        assert ware is not None
        assert ware.get("id") == "my_ware"

    def test_wares_diff_has_price(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware(
            "my_ware",
            "My Custom Ware",
            out,
            price_min=500,
            price_avg=1000,
            price_max=1500,
        )
        root = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = root.find(".//ware[@id='my_ware']")
        assert ware is not None
        price = ware.find("price")
        assert price is not None
        assert price.get("min") == "500"
        assert price.get("average") == "1000"
        assert price.get("max") == "1500"

    def test_generates_translation(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        t_file = out / "t" / "0001-l044.xml"
        assert t_file.exists()
        root = ET.parse(t_file).getroot()
        assert root.tag == "language"

    def test_translation_has_name(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware(
            "my_ware",
            "My Custom Ware",
            out,
            description="A test ware",
            price_avg=1000,
        )
        root = ET.parse(out / "t" / "0001-l044.xml").getroot()
        page = root.find("page")
        assert page is not None
        texts = {t.get("id"): t.text for t in page.findall("t")}
        assert "My Custom Ware" in texts.values()
        assert "A test ware" in texts.values()

    def test_uses_page_id_90000_plus(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        root = ET.parse(out / "t" / "0001-l044.xml").getroot()
        page = root.find("page")
        assert page is not None
        page_id = int(page.get("id", "0"))
        assert page_id >= 90000

    def test_ware_refs_translation(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        wroot = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = wroot.find(".//ware[@id='my_ware']")
        assert ware is not None
        name_ref = ware.get("name", "")
        assert name_ref.startswith("{9000")

    def test_no_extra_files(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware("my_ware", "My Custom Ware", out, price_avg=1000)
        all_files = list(out.rglob("*"))
        xml_files = [f for f in all_files if f.is_file()]
        assert len(xml_files) == 2  # wares.xml + translation

    def test_with_group_and_volume(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        scaffold_ware(
            "my_ware",
            "My Custom Ware",
            out,
            price_avg=1000,
            group="hightech",
            volume=20,
        )
        wroot = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = wroot.find(".//ware[@id='my_ware']")
        assert ware is not None
        assert ware.get("group") == "hightech"
        assert ware.get("volume") == "20"


# --- scaffold equipment (Tier 2) ---


class TestScaffoldEquipment:
    def test_generates_four_files(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        assert (out / "libraries" / "wares.xml").exists()
        assert (out / "index" / "macros.xml").exists()
        assert (out / "t" / "0001-l044.xml").exists()
        # Macro file
        macro_files = list(out.rglob("*_macro.xml"))
        macro_files = [f for f in macro_files if "index" not in str(f)]
        assert len(macro_files) == 1

    def test_cloned_macro_has_new_name(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        macro_files = [
            f
            for f in out.rglob("*_macro.xml")
            if "index" not in str(f) and "libraries" not in str(f)
        ]
        root = ET.parse(macro_files[0]).getroot()
        macro = root.find("macro")
        assert macro is not None
        assert macro.get("name") == "my_engine_macro"

    def test_cloned_macro_preserves_properties(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        macro_files = [
            f
            for f in out.rglob("*_macro.xml")
            if "index" not in str(f) and "libraries" not in str(f)
        ]
        root = ET.parse(macro_files[0]).getroot()
        macro = root.find("macro")
        assert macro is not None
        hull = macro.find(".//hull")
        assert hull is not None
        assert hull.get("max") == "500"

    def test_index_diff_registers_macro(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        root = ET.parse(out / "index" / "macros.xml").getroot()
        assert root.tag == "diff"
        add = root.find("add")
        assert add is not None
        entry = add.find("entry")
        assert entry is not None
        assert entry.get("name") == "my_engine_macro"

    def test_wares_diff_refs_macro(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        root = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = root.find(".//ware")
        assert ware is not None
        comp = ware.find("component")
        assert comp is not None
        assert comp.get("ref") == "my_engine_macro"

    def test_ids_consistent(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_equipment(
            "my_engine_macro",
            "My Engine",
            out,
            clone_from="engine_test_mk1_macro",
            db_path=db,
        )
        # Ware ID should be macro name without _macro suffix
        root = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = root.find(".//ware")
        assert ware is not None
        assert ware.get("id") == "my_engine"

    def test_clone_from_not_found_raises(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        import pytest

        with pytest.raises(ValueError, match="not found"):
            scaffold_equipment(
                "my_engine_macro",
                "My Engine",
                out,
                clone_from="nonexistent_macro",
                db_path=db,
            )


# --- CLI ---


class TestScaffoldCli:
    def test_scaffold_ware_cli(self, tmp_path: Path) -> None:
        out = tmp_path / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "scaffold",
                "ware",
                "--id",
                "cli_ware",
                "--name",
                "CLI Ware",
                "--price-avg",
                "500",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "libraries" / "wares.xml").exists()
        assert (out / "t" / "0001-l044.xml").exists()

    def test_scaffold_equipment_cli(self, tmp_path: Path) -> None:
        game, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "scaffold",
                "equipment",
                "--id",
                "cli_engine_macro",
                "--name",
                "CLI Engine",
                "--clone-from",
                "engine_test_mk1_macro",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "libraries" / "wares.xml").exists()
        assert (out / "index" / "macros.xml").exists()

    def test_scaffold_equipment_no_clone_errors(self, tmp_path: Path) -> None:
        game, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "scaffold",
                "equipment",
                "--id",
                "my_thing_macro",
                "--name",
                "My Thing",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "clone-from" in result.stderr.lower()


# --- scaffold ship (Tier 3) ---


class TestScaffoldShip:
    def test_generates_all_files(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        files = scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
            size="s",
        )
        assert (out / "libraries" / "wares.xml").exists()
        assert (out / "index" / "macros.xml").exists()
        assert (out / "index" / "components.xml").exists()
        assert (out / "t" / "0001-l044.xml").exists()
        assert (out / "README_SHIP.md").exists()
        assert len(files) == 6

    def test_ship_macro_has_correct_class(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        macro_file = (
            out / "assets" / "units" / "size_s" / "macros" / "mymod_fighter_01_a_macro.xml"
        )
        assert macro_file.exists()
        root = ET.parse(macro_file).getroot()
        macro = root.find("macro")
        assert macro is not None
        assert macro.get("class") == "ship_s"
        assert macro.get("name") == "mymod_fighter_01_a_macro"

    def test_ship_macro_preserves_properties(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        macro_file = (
            out / "assets" / "units" / "size_s" / "macros" / "mymod_fighter_01_a_macro.xml"
        )
        root = ET.parse(macro_file).getroot()
        hull = root.find(".//hull")
        assert hull is not None
        assert hull.get("max") == "3100"

    def test_component_index_diff(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        root = ET.parse(out / "index" / "components.xml").getroot()
        assert root.tag == "diff"
        entry = root.find(".//entry")
        assert entry is not None
        assert entry.get("name") == "mymod_fighter_01"

    def test_ware_is_ship_transport(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        root = ET.parse(out / "libraries" / "wares.xml").getroot()
        ware = root.find(".//ware")
        assert ware is not None
        assert ware.get("transport") == "ship"
        assert ware.get("tags") == "ship"

    def test_readme_mentions_component(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        readme = (out / "README_SHIP.md").read_text()
        assert "component" in readme.lower()
        assert "3D model" in readme or "3d model" in readme.lower()

    def test_readme_documents_stat_mod_workflow(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        scaffold_ship(
            "mymod_fighter_01_a_macro",
            "My Fighter",
            out,
            clone_from="ship_test_s_fighter_01_a_macro",
            db_path=db,
        )
        readme = (out / "README_SHIP.md").read_text()
        assert "extract-macro" in readme
        assert "xmldiff" in readme
        assert "modify an existing ship" in readme.lower()


class TestScaffoldShipCli:
    def test_scaffold_ship_cli(self, tmp_path: Path) -> None:
        _, db = make_indexed_game_dir(tmp_path)
        out = tmp_path / "src"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "--db",
                str(db),
                "scaffold",
                "ship",
                "--id",
                "cli_ship_macro",
                "--name",
                "CLI Ship",
                "--clone-from",
                "ship_test_s_fighter_01_a_macro",
                "--size",
                "s",
                "-o",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "libraries" / "wares.xml").exists()
        assert (out / "index" / "components.xml").exists()
