"""Tests for x4cat init scaffolding."""

from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import pytest

from x4_catalog._init import scaffold_project

if TYPE_CHECKING:
    from pathlib import Path


class TestScaffoldProject:
    def test_creates_project_directory(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert out.is_dir()

    def test_content_xml_has_correct_id(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        root = ET.parse(out / "content.xml").getroot()
        assert root.get("id") == "my_mod"

    def test_content_xml_has_author(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, author="Test Author")
        root = ET.parse(out / "content.xml").getroot()
        assert root.get("author") == "Test Author"

    def test_content_xml_has_description(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, description="A test mod")
        root = ET.parse(out / "content.xml").getroot()
        assert root.get("description") == "A test mod"

    def test_content_xml_has_game_version(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, game_version=700)
        root = ET.parse(out / "content.xml").getroot()
        dep = root.find("dependency")
        assert dep is not None
        assert dep.get("version") == "700"

    def test_pyproject_has_correct_name(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        text = (out / "pyproject.toml").read_text()
        assert 'name = "my-mod"' in text

    def test_pyproject_has_repo_url_full(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, repo="https://github.com/user/my_mod")
        text = (out / "pyproject.toml").read_text()
        assert "https://github.com/user/my_mod" in text

    def test_pyproject_has_repo_url_shorthand(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, repo="user/my_mod")
        text = (out / "pyproject.toml").read_text()
        assert "https://github.com/user/my_mod" in text

    def test_pyproject_no_repo_url_when_not_provided(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        text = (out / "pyproject.toml").read_text()
        assert "Repository" not in text

    def test_readme_has_mod_id(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        text = (out / "README.md").read_text()
        assert "# my_mod" in text
        assert "extension_poc" not in text

    def test_src_directories_created(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert (out / "src" / "md").is_dir()
        assert (out / "src" / "aiscripts").is_dir()
        assert (out / "src" / "libraries").is_dir()

    def test_md_script_renamed(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert (out / "src" / "md" / "my_mod.xml").is_file()
        assert not (out / "src" / "md" / "extension_poc.xml").exists()

    def test_md_script_content_substituted(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        text = (out / "src" / "md" / "my_mod.xml").read_text()
        assert "extension_poc" not in text.lower()
        assert "MyMod" in text or "my_mod" in text

    def test_makefile_exists(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert (out / "Makefile").is_file()

    def test_tests_exist(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert (out / "tests" / "test_mod.py").is_file()
        assert (out / "tests" / "__init__.py").is_file()

    def test_gitignore_exists(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        assert (out / ".gitignore").is_file()

    def test_no_template_artifacts(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out)
        # Should not contain template-specific files
        assert not (out / ".git").exists()
        assert not (out / "uv.lock").exists()
        assert not (out / "LICENSE").exists()

    def test_existing_directory_raises(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        out.mkdir()
        (out / "something").write_text("exists")
        with pytest.raises(FileExistsError):
            scaffold_project("my_mod", output_dir=out)

    def test_git_init(self, tmp_path: Path) -> None:
        out = tmp_path / "my_mod"
        scaffold_project("my_mod", output_dir=out, init_git=True)
        assert (out / ".git").is_dir()


# --- CLI integration ---


class TestInitCli:
    def test_init_subcommand(self, tmp_path: Path) -> None:
        out = tmp_path / "cli_mod"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "init",
                "cli_mod",
                "-o",
                str(out),
                "--author",
                "CLI Test",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / "content.xml").exists()
        root = ET.parse(out / "content.xml").getroot()
        assert root.get("id") == "cli_mod"
        assert root.get("author") == "CLI Test"

    def test_init_with_repo_shorthand(self, tmp_path: Path) -> None:
        out = tmp_path / "repo_mod"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "init",
                "repo_mod",
                "-o",
                str(out),
                "--repo",
                "user/repo_mod",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        text = (out / "pyproject.toml").read_text()
        assert "https://github.com/user/repo_mod" in text

    def test_init_with_git(self, tmp_path: Path) -> None:
        out = tmp_path / "git_mod"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "x4_catalog",
                "init",
                "git_mod",
                "-o",
                str(out),
                "--git",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (out / ".git").is_dir()
