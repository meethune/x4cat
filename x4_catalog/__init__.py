"""X4 catalog reader — XRCatTool equivalent for Linux."""

from x4_catalog._conflicts import check_conflicts
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
    read_payload,
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
from x4_catalog._scaffold import scaffold_equipment, scaffold_ship, scaffold_ware
from x4_catalog._schema_extract import extract_schema_to_db, extract_scriptproperties_to_db
from x4_catalog._schema_validate import validate_schema
from x4_catalog._search import search_assets
from x4_catalog._translations import scaffold_translation, validate_translations
from x4_catalog._types import ConflictEntry, ConflictReport, ValidationReport
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
    "check_conflicts",
    "ConflictEntry",
    "ConflictReport",
    "DiffOp",
    "FileValidationReport",
    "ValidationResult",
    "build_index",
    "build_vfs",
    "build_vfs_multi",
    "diff_and_pack",
    "diff_file_sets",
    "extract_macro",
    "extract_schema_to_db",
    "extract_scriptproperties_to_db",
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
    "read_payload",
    "scaffold_equipment",
    "scaffold_project",
    "scaffold_ship",
    "scaffold_translation",
    "scaffold_ware",
    "search_assets",
    "ValidationReport",
    "validate_diff_directory",
    "validate_schema",
    "validate_diff_file",
    "validate_translations",
]
