"""Shared XML utility functions."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    """Indent an element tree for pretty printing (in-place)."""
    ind = "\n" + "  " * (level + 1)
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = ind
        for i, child in enumerate(elem):
            indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = ind if i < len(elem) - 1 else "\n" + "  " * level
    if not elem.tail or not elem.tail.strip():
        elem.tail = "\n" + "  " * level


def write_xml(path: Any, root: ET.Element) -> None:
    """Write an XML element to a file with declaration and indentation."""
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    indent_xml(root)
    data = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        + ET.tostring(root, encoding="unicode").encode()
    )
    p.write_bytes(data)
