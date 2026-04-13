"""Shared fixtures for X4 catalog tests."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _write_cat_dat(
    directory: Path,
    cat_name: str,
    entries: list[tuple[str, bytes, int]],
) -> None:
    """Write a paired .cat/.dat file.

    entries: list of (virtual_path, content_bytes, mtime).
    """
    cat_lines: list[str] = []
    dat_blob = bytearray()
    for vpath, content, mtime in entries:
        cat_lines.append(f"{vpath} {len(content)} {mtime} {_md5(content)}")
        dat_blob.extend(content)
    (directory / cat_name).write_text("\n".join(cat_lines) + "\n", encoding="utf-8")
    (directory / cat_name.replace(".cat", ".dat")).write_bytes(bytes(dat_blob))


@pytest.fixture()
def game_dir(tmp_path: Path) -> Path:
    """Minimal fake game install with two numbered catalogs.

    01.cat/dat has: md/test.xml, libraries/wares.xml
    02.cat/dat has: md/test.xml (override), aiscripts/order.trade.xml
    """
    _write_cat_dat(
        tmp_path,
        "01.cat",
        [
            ("md/test.xml", b"<md>original</md>", 1000000),
            ("libraries/wares.xml", b"<wares/>", 1000001),
        ],
    )
    _write_cat_dat(
        tmp_path,
        "02.cat",
        [
            ("md/test.xml", b"<md>updated</md>", 2000000),
            ("aiscripts/order.trade.xml", b"<aiscript/>", 2000001),
        ],
    )
    return tmp_path


@pytest.fixture()
def ext_dir(game_dir: Path) -> Path:
    """Add a DLC-like extension to the game dir."""
    ext = game_dir / "extensions" / "ego_dlc_test"
    ext.mkdir(parents=True)
    (ext / "content.xml").write_text(
        '<?xml version="1.0"?>\n'
        '<content id="ego_dlc_test" name="Test DLC" version="100">\n'
        '  <dependency version="100" />\n'
        "</content>\n",
        encoding="utf-8",
    )
    _write_cat_dat(
        ext,
        "ext_01.cat",
        [
            ("md/dlc_mission.xml", b"<md>dlc</md>", 3000000),
            ("libraries/wares.xml", b"<wares>dlc</wares>", 3000001),
        ],
    )
    return ext
