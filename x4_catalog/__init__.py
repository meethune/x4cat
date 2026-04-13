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

__all__ = [
    "CatEntry",
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
]
