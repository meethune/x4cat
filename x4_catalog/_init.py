"""Scaffold a new X4 mod project from the extension_poc template."""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "extension_poc"

_MOD_ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")

# Files to copy from the template (relative to template root).
_COPY_FILES = [
    "content.xml",
    "Makefile",
    "pyproject.toml",
    "README.md",
    ".gitignore",
    "tests/__init__.py",
    "tests/test_mod.py",
]

# Directories to create (even if empty in template).
_ENSURE_DIRS = [
    "src/md",
    "src/aiscripts",
    "src/libraries",
    "tests",
]

# Files that need text substitution.
_SUBSTITUTE_FILES = (
    "content.xml",
    "pyproject.toml",
    "README.md",
    "tests/test_mod.py",
)


def _to_pascal_case(mod_id: str) -> str:
    """Convert ``my_mod_name`` to ``MyModName``."""
    return "".join(word.capitalize() for word in mod_id.split("_"))


def _expand_repo_url(repo: str) -> str:
    """Expand GitHub shorthand ``user/repo`` to full URL."""
    if repo.startswith(("http://", "https://")):
        return repo
    if "/" in repo and not repo.startswith("/"):
        return f"https://github.com/{repo}"
    return repo


def _xml_attr_escape(value: str) -> str:
    """Escape a string for safe use inside an XML attribute value (double-quoted)."""
    return xml_escape(value, entities={'"': "&quot;"})


def _git_config_get(key: str) -> str | None:
    """Read a git config value, returning None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "config", key],
            capture_output=True,
            text=True,
            check=False,
        )
        val = result.stdout.strip()
        return val if val else None
    except FileNotFoundError:
        return None


def scaffold_project(
    mod_id: str,
    *,
    output_dir: Path | None = None,
    author: str | None = None,
    description: str | None = None,
    game_version: int = 900,
    repo: str | None = None,
    init_git: bool = False,
) -> Path:
    """Create a new X4 mod project from the extension_poc template.

    Returns the path to the created project directory.
    Raises ``FileExistsError`` if the output directory already exists and is non-empty.
    Raises ``ValueError`` if ``mod_id`` contains invalid characters.
    """
    if not _MOD_ID_RE.match(mod_id):
        raise ValueError(
            f"Invalid mod_id: {mod_id!r} "
            "(must start with a letter, contain only alphanumeric/underscores, max 64 chars)"
        )

    out = output_dir or Path.cwd() / mod_id

    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Directory already exists and is not empty: {out}")

    if not _TEMPLATE_DIR.is_dir():
        raise RuntimeError(
            f"Template not found at {_TEMPLATE_DIR}. "
            "Run 'git submodule update --init' to fetch it."
        )

    # Resolve defaults
    if author is None and init_git:
        author = _git_config_get("user.name")
    if author is None:
        author = ""
    if description is None:
        description = "X4: Foundations extension mod"

    today = datetime.now(UTC).date().isoformat()
    mod_name_hyphen = mod_id.replace("_", "-")
    pascal_name = _to_pascal_case(mod_id)
    repo_url = _expand_repo_url(repo) if repo else None

    # Escape user-supplied strings for XML attribute safety
    safe_author = _xml_attr_escape(author)
    safe_description = _xml_attr_escape(description)

    # Create directories
    for d in _ENSURE_DIRS:
        (out / d).mkdir(parents=True, exist_ok=True)

    # Copy and process files
    for rel_path in _COPY_FILES:
        src = _TEMPLATE_DIR / rel_path
        if not src.exists():
            continue
        dest = out / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    # Copy MD script with renamed filename
    template_md = _TEMPLATE_DIR / "src" / "md" / "extension_poc.xml"
    md_rel_path: str | None = None
    if template_md.exists():
        md_rel_path = f"src/md/{mod_id}.xml"
        dest_md = out / md_rel_path
        shutil.copy2(template_md, dest_md)

    # Build the list of files to substitute (local copy — never mutate module state)
    substitute_files = list(_SUBSTITUTE_FILES)
    if md_rel_path:
        substitute_files.append(md_rel_path)

    # Apply substitutions
    for rel_path in substitute_files:
        fpath = out / rel_path
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")

        # content.xml specific substitutions (use escaped values for XML attributes)
        text = text.replace('id="extension_poc"', f'id="{mod_id}"')
        text = text.replace('name="Extension PoC"', f'name="{mod_id}"')
        text = text.replace(
            'description="Proof of concept X4 extension mod"',
            f'description="{safe_description}"',
        )
        text = text.replace('author="Meethune Bhowmick"', f'author="{safe_author}"')
        text = text.replace('date="2026-04-13"', f'date="{today}"')
        text = re.sub(
            r'<dependency version="\d+" />',
            f'<dependency version="{game_version}" />',
            text,
        )

        # pyproject.toml substitutions (plain text, not XML)
        text = text.replace('name = "extension-poc"', f'name = "{mod_name_hyphen}"')
        text = text.replace(
            'description = "Proof of concept X4: Foundations extension mod"',
            f'description = "{description}"',
        )
        if repo_url:
            text = text.replace(
                "https://github.com/meethune/extension_poc",
                repo_url,
            )
        else:
            # Remove the repository URL section entirely
            text = re.sub(
                r"\[project\.urls\]\nRepository = \"[^\"]*\"\n\n",
                "",
                text,
            )

        # General substitutions (order matters — longer patterns first)
        text = text.replace("Extension PoC", mod_id)
        text = text.replace("extension_poc", mod_id)
        text = text.replace("extension-poc", mod_name_hyphen)
        text = text.replace("ExtensionPoC", pascal_name)

        fpath.write_text(text, encoding="utf-8")

    # Initialize git repo
    if init_git:
        subprocess.run(["git", "init", str(out)], capture_output=True, check=True)

    return out
