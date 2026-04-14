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
from x4_catalog._extract_macro import extract_macro
from x4_catalog._index import (
    build_index,
    db_path_for_game_dir,
    find_index_db,
    is_index_stale,
    open_index,
)
from x4_catalog._init import scaffold_project
from x4_catalog._inspect import inspect_asset
from x4_catalog._search import search_assets
from x4_catalog._validate import (
    DiffOp,
    FileValidationReport,
    ValidationResult,
    validate_diff_directory,
    validate_diff_file,
)
from x4_catalog._xmldiff import generate_diff

__all__ = [
    "CatEntry",
    "DiffOp",
    "FileValidationReport",
    "ValidationResult",
    "build_index",
    "build_vfs",
    "build_vfs_multi",
    "diff_and_pack",
    "diff_file_sets",
    "extract_macro",
    "extract_to_disk",
    "db_path_for_game_dir",
    "find_index_db",
    "generate_diff",
    "inspect_asset",
    "is_index_stale",
    "iter_cat_files",
    "list_entries",
    "main",
    "open_index",
    "pack_catalog",
    "parse_cat_line",
    "scaffold_project",
    "search_assets",
    "validate_diff_directory",
    "validate_diff_file",
]
