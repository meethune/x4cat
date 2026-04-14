"""X4 catalog reader — XRCatTool equivalent for Linux."""

from x4_catalog._core import (
    CatEntry,
    build_vfs,
    build_vfs_multi,
    diff_and_pack,
    diff_file_sets,
    extract_to_disk,
    iter_cat_files,
    list_entries,
    main,
    pack_catalog,
    parse_cat_line,
)
from x4_catalog._validate import (
    DiffOp,
    FileValidationReport,
    ValidationResult,
    validate_diff_directory,
    validate_diff_file,
)

__all__ = [
    "CatEntry",
    "DiffOp",
    "FileValidationReport",
    "ValidationResult",
    "build_vfs",
    "build_vfs_multi",
    "diff_and_pack",
    "diff_file_sets",
    "extract_to_disk",
    "iter_cat_files",
    "list_entries",
    "main",
    "pack_catalog",
    "parse_cat_line",
    "validate_diff_directory",
    "validate_diff_file",
]
