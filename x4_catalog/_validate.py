"""Validate X4 XML diff patches against base game files.

Checks that every ``sel`` and ``if`` XPath in a diff patch matches
at least one element in the corresponding base game XML.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from x4_catalog._core import build_vfs, read_payload

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

_DIFF_OPS = frozenset({"add", "replace", "remove"})


@dataclass(frozen=True, slots=True)
class DiffOp:
    """A single operation parsed from a diff patch file."""

    tag: str
    sel: str
    pos: str = ""
    type_attr: str = ""
    if_cond: str = ""
    line: int = 0


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating one diff operation."""

    op: DiffOp
    sel_matched: bool
    if_matched: bool | None = None
    sel_detail: str = ""
    if_detail: str = ""


@dataclass(frozen=True, slots=True)
class FileValidationReport:
    """Validation results for one diff patch file."""

    diff_file: Path
    virtual_path: str
    base_found: bool
    parse_error: str | None = None
    results: list[ValidationResult] = field(default_factory=list)


# --- Diff parsing ---


def parse_diff_ops(data: bytes) -> list[DiffOp]:
    """Parse a diff patch file and extract all operations with line numbers.

    Raises ``ValueError`` on malformed XML or invalid diff structure.
    """
    ops: list[DiffOp] = []
    depth = 0
    root_tag: str | None = None
    current_attrs: dict[str, str] = {}
    current_tag: str = ""
    current_line: int = 0

    parser = expat.ParserCreate()
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)

    def _reject_entity_decl(*_args: object) -> None:
        raise ValueError("Entity declarations are not allowed in diff patches")

    parser.EntityDeclHandler = _reject_entity_decl

    def _start(tag: str, attrs: dict[str, str]) -> None:
        nonlocal depth, root_tag, current_attrs, current_tag, current_line
        depth += 1
        if depth == 1:
            root_tag = tag
        elif depth == 2:
            current_tag = tag
            current_attrs = attrs
            current_line = parser.CurrentLineNumber

    def _end(_tag: str) -> None:
        nonlocal depth
        if depth == 2 and root_tag == "diff":
            if current_tag not in _DIFF_OPS:
                depth -= 1
                return
            sel = current_attrs.get("sel")
            if sel is None:
                raise ValueError(
                    f"Line {current_line}: <{current_tag}> missing required 'sel' attribute"
                )
            ops.append(
                DiffOp(
                    tag=current_tag,
                    sel=sel,
                    pos=current_attrs.get("pos", ""),
                    type_attr=current_attrs.get("type", ""),
                    if_cond=current_attrs.get("if", ""),
                    line=current_line,
                )
            )
        depth -= 1

    parser.StartElementHandler = _start
    parser.EndElementHandler = _end

    try:
        parser.Parse(data, True)
    except expat.ExpatError as exc:
        raise ValueError(f"XML parse error: {exc}") from exc

    if root_tag != "diff":
        raise ValueError(f"Expected root element <diff>, got <{root_tag}>")

    return ops


# --- XPath evaluation ---


def _split_trailing_attr(xpath: str) -> tuple[str, str | None]:
    """Split ``/path/@attr`` into ``('/path', 'attr')``.

    Returns ``(xpath, None)`` if the path doesn't end with ``/@attr``.
    """
    if "/@" not in xpath:
        return xpath, None
    last_slash = xpath.rfind("/")
    segment = xpath[last_slash + 1 :]
    if segment.startswith("@"):
        return xpath[:last_slash], segment[1:]
    return xpath, None


def _split_root(xpath: str) -> tuple[str, str]:
    """Split ``/root/rest`` into ``('root', 'rest')``.

    Returns ``('root', '')`` if the path is just ``/root``.
    Handles predicates on the root element: ``/root[@a='b']/rest`` ->
    ``('root', 'rest')`` with predicates stripped from root tag.
    """
    path = xpath.lstrip("/")
    # Find the end of the first path segment (could have predicates)
    bracket_depth = 0
    for i, ch in enumerate(path):
        if ch == "[":
            bracket_depth += 1
        elif ch == "]":
            bracket_depth -= 1
        elif ch == "/" and bracket_depth == 0:
            return path[:i], path[i + 1 :]
    return path, ""


def _root_tag_name(segment: str) -> str:
    """Extract the bare tag name from a segment that may include predicates."""
    bracket = segment.find("[")
    if bracket != -1:
        return segment[:bracket]
    return segment


def evaluate_xpath(base_data: bytes, xpath: str) -> tuple[bool, str]:
    """Evaluate an XPath expression against base game XML.

    Returns ``(matched, detail)`` where *detail* describes the result.
    For unsupported XPath features, returns a warning detail instead of crashing.
    """
    try:
        root = ET.fromstring(base_data)
    except ET.ParseError as exc:
        return False, f"base XML parse error: {exc}"

    # Handle trailing /@attr
    xpath_elem, trailing_attr = _split_trailing_attr(xpath)

    # Split into root segment and rest
    root_segment, rest = _split_root(xpath_elem)
    root_tag = _root_tag_name(root_segment)

    # Check root element matches
    if root_tag != root.tag:
        return False, f"root element mismatch: expected <{root_tag}>, found <{root.tag}>"

    # If the path is just /root (possibly with predicates)
    if not rest:
        if trailing_attr:
            if root.get(trailing_attr) is not None:
                return True, f"attribute @{trailing_attr} found on root"
            return False, f"attribute @{trailing_attr} not found on root"
        return True, "root element matched"

    # Evaluate the rest as a relative path from root
    try:
        if trailing_attr:
            matches = root.findall(rest)
            if not matches:
                return False, f"no elements matched: {rest}"
            for m in matches:
                if m.get(trailing_attr) is not None:
                    return True, f"@{trailing_attr} found ({len(matches)} element(s) matched)"
            return False, f"@{trailing_attr} not found on matched elements"

        matches = root.findall(rest)
        if matches:
            return True, f"{len(matches)} element(s) matched"
        return False, f"no elements matched: {rest}"
    except SyntaxError:
        return False, f"unsupported XPath syntax: {xpath} (requires lxml for evaluation)"


# --- File-level validation ---


def validate_diff_file(
    diff_data: bytes,
    base_data: bytes,
    diff_path: Path,
    virtual_path: str,
) -> FileValidationReport:
    """Validate a single diff patch against its base game XML."""
    try:
        ops = parse_diff_ops(diff_data)
    except ValueError as exc:
        return FileValidationReport(
            diff_file=diff_path,
            virtual_path=virtual_path,
            base_found=True,
            parse_error=str(exc),
        )

    results: list[ValidationResult] = []
    for op in ops:
        sel_matched, sel_detail = evaluate_xpath(base_data, op.sel)

        if_matched: bool | None = None
        if_detail = ""
        if op.if_cond:
            if_matched, if_detail = evaluate_xpath(base_data, op.if_cond)

        results.append(
            ValidationResult(
                op=op,
                sel_matched=sel_matched,
                if_matched=if_matched,
                sel_detail=sel_detail,
                if_detail=if_detail,
            )
        )

    return FileValidationReport(
        diff_file=diff_path,
        virtual_path=virtual_path,
        base_found=True,
        results=results,
    )


# --- Directory-level validation ---


def _is_diff_xml(path: Path) -> bool:
    """Check if a file is an XML diff patch (has ``<diff>`` root element)."""
    try:
        for _event, elem in ET.iterparse(path, events=("start",)):
            return elem.tag == "diff"
    except ET.ParseError:
        return False
    return False


def validate_diff_directory(
    game_dir: Path,
    mod_dir: Path,
    prefix: str = "",
) -> list[FileValidationReport]:
    """Validate all diff patches in *mod_dir* against base game files.

    Returns a list of reports, one per diff patch file found.
    Non-diff XML files and non-XML files are silently skipped.
    """
    vfs = build_vfs(game_dir, prefix=prefix)
    reports: list[FileValidationReport] = []

    for xml_path in sorted(mod_dir.rglob("*.xml")):
        if not xml_path.is_file() or xml_path.is_symlink():
            continue
        if not _is_diff_xml(xml_path):
            continue

        virtual_path = xml_path.relative_to(mod_dir).as_posix()
        entry = vfs.get(virtual_path)

        if entry is None:
            reports.append(
                FileValidationReport(
                    diff_file=xml_path,
                    virtual_path=virtual_path,
                    base_found=False,
                )
            )
            continue

        base_data = read_payload(entry)
        diff_data = xml_path.read_bytes()
        reports.append(validate_diff_file(diff_data, base_data, xml_path, virtual_path))

    return reports
