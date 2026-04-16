"""Shared typed return types for validation and inspection functions."""

from __future__ import annotations

from typing import TypedDict


class ValidationReport(TypedDict):
    """Return type for validation functions (translations, schema)."""

    errors: list[str]
    warnings: list[str]


class ConflictEntry(TypedDict):
    """A single conflict or overlap between mods."""

    file: str
    sel: str
    mods: list[str]
    operations: dict[str, list[str]]


class ConflictReport(TypedDict):
    """Return type for check_conflicts()."""

    conflicts: list[ConflictEntry]
    safe: list[ConflictEntry]
    info: list[ConflictEntry]
    files_checked: int
