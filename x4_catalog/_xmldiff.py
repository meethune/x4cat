"""Generate X4-compatible XML diff patches from two XML files.

Compares a base XML file with a modified copy and emits a ``<diff>``
document with ``<add>``, ``<replace>``, and ``<remove>`` operations.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from x4_catalog._xml_utils import indent_xml as _indent

_IDENTITY_ATTRS = ("id", "name")


def _element_key(elem: ET.Element) -> str:
    """Return a stable identity key for an element.

    Uses ``@id``, then ``@name``, then falls back to tag+position placeholder.
    """
    for attr in _IDENTITY_ATTRS:
        val = elem.get(attr)
        if val is not None:
            return f"{elem.tag}[@{attr}='{val}']"
    return ""


def _build_index(parent: ET.Element) -> dict[str, ET.Element]:
    """Index children by their identity key.  Only elements with a key are indexed."""
    index: dict[str, ET.Element] = {}
    for child in parent:
        key = _element_key(child)
        if key:
            index[key] = child
    return index


def _xpath_for(path_parts: list[str]) -> str:
    """Build an XPath selector from accumulated path parts."""
    return "/" + "/".join(path_parts)


def _elements_equal(a: ET.Element, b: ET.Element) -> bool:
    """Deep equality check for two elements (tag, attribs, text, tail, children)."""
    if a.tag != b.tag:
        return False
    if a.attrib != b.attrib:
        return False
    if (a.text or "").strip() != (b.text or "").strip():
        return False
    if (a.tail or "").strip() != (b.tail or "").strip():
        return False
    if len(a) != len(b):
        return False
    return all(_elements_equal(ac, bc) for ac, bc in zip(a, b, strict=True))


def _diff_element(
    base: ET.Element,
    mod: ET.Element,
    path_parts: list[str],
    ops: list[ET.Element],
) -> None:
    """Recursively compare two elements and emit diff operations."""
    # Attribute changes
    base_attrs = dict(base.attrib)
    mod_attrs = dict(mod.attrib)

    parent_xpath = _xpath_for(path_parts)

    for attr, mod_val in sorted(mod_attrs.items()):
        base_val = base_attrs.get(attr)
        if base_val is None:
            # New attribute
            op = ET.Element("add", sel=parent_xpath, type=f"@{attr}")
            op.text = mod_val
            ops.append(op)
        elif base_val != mod_val:
            # Changed attribute
            op = ET.Element("replace", sel=f"{parent_xpath}/@{attr}")
            op.text = mod_val
            ops.append(op)

    for attr in sorted(base_attrs):
        if attr not in mod_attrs:
            # Removed attribute
            op = ET.Element("remove", sel=f"{parent_xpath}/@{attr}")
            ops.append(op)

    # Text content changes
    base_text = (base.text or "").strip()
    mod_text = (mod.text or "").strip()
    if base_text != mod_text and mod_text:
        op = ET.Element("replace", sel=f"{parent_xpath}/text()")
        op.text = mod_text
        ops.append(op)

    # Child element changes
    base_index = _build_index(base)
    mod_index = _build_index(mod)
    base_children = list(base)
    mod_children = list(mod)

    # Handle keyed elements (with @id or @name)
    base_keyed = set(base_index.keys())
    mod_keyed = set(mod_index.keys())

    # Removed keyed elements
    for key in sorted(base_keyed - mod_keyed):
        op = ET.Element("remove", sel=f"{parent_xpath}/{key}")
        ops.append(op)

    # Added keyed elements
    for key in sorted(mod_keyed - base_keyed):
        op = ET.Element("add", sel=parent_xpath)
        child_copy = _deep_copy(mod_index[key])
        op.append(child_copy)
        ops.append(op)

    # Modified keyed elements — recurse
    for key in sorted(base_keyed & mod_keyed):
        base_child = base_index[key]
        mod_child = mod_index[key]
        if not _elements_equal(base_child, mod_child):
            _diff_element(base_child, mod_child, path_parts + [key], ops)

    # Handle un-keyed elements by position
    base_unkeyed = [c for c in base_children if not _element_key(c)]
    mod_unkeyed = [c for c in mod_children if not _element_key(c)]

    # Match un-keyed elements by tag and position
    base_by_tag: dict[str, list[ET.Element]] = {}
    for c in base_unkeyed:
        base_by_tag.setdefault(c.tag, []).append(c)

    mod_by_tag: dict[str, list[ET.Element]] = {}
    for c in mod_unkeyed:
        mod_by_tag.setdefault(c.tag, []).append(c)

    all_tags = sorted(set(list(base_by_tag.keys()) + list(mod_by_tag.keys())))
    for tag in all_tags:
        b_list = base_by_tag.get(tag, [])
        m_list = mod_by_tag.get(tag, [])

        # Pair up by position
        for i, (bc, mc) in enumerate(zip(b_list, m_list, strict=False)):
            if not _elements_equal(bc, mc):
                pos_key = f"{tag}[{i + 1}]" if len(b_list) > 1 else tag
                _diff_element(bc, mc, path_parts + [pos_key], ops)

        # Extra elements in mod = additions
        for mc in m_list[len(b_list) :]:
            op = ET.Element("add", sel=parent_xpath)
            op.append(_deep_copy(mc))
            ops.append(op)

        # Extra elements in base = removals
        for i in range(len(m_list), len(b_list)):
            pos_key = f"{tag}[{i + 1}]" if len(b_list) > 1 else tag
            op = ET.Element("remove", sel=f"{parent_xpath}/{pos_key}")
            ops.append(op)


def _deep_copy(elem: ET.Element) -> ET.Element:
    """Create a deep copy of an element."""
    copy = ET.Element(elem.tag, elem.attrib)
    copy.text = elem.text
    copy.tail = elem.tail
    for child in elem:
        copy.append(_deep_copy(child))
    return copy


def generate_diff(base_data: bytes, mod_data: bytes) -> bytes:
    """Generate an X4-compatible diff patch from two XML files.

    Returns the diff XML as bytes.
    """
    base_root = ET.fromstring(base_data)
    mod_root = ET.fromstring(mod_data)

    if base_root.tag != mod_root.tag:
        raise ValueError(
            f"Root element mismatch: base has <{base_root.tag}>, mod has <{mod_root.tag}>"
        )

    ops: list[ET.Element] = []
    _diff_element(base_root, mod_root, [base_root.tag], ops)

    diff = ET.Element("diff")
    diff.text = "\n  " if ops else "\n"
    for op in ops:
        _indent(op, level=1)
        diff.append(op)

    return (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        + ET.tostring(diff, encoding="unicode").encode()
    )
