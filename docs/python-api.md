---
title: "Python API"
layout: default
nav_order: 4
has_children: true
---

# Python API

All public functions and types are importable from `x4_catalog`:

```python
from x4_catalog import build_vfs, inspect_asset, scaffold_ware, ...
```

## Sections

| Section | Contents |
|---------|----------|
| [Core Types](core-types) | CatEntry, DiffOp, ValidationResult, FileValidationReport, ValidationReport, ConflictEntry, ConflictReport |
| [Archive Functions](archive-functions) | build_vfs, list_entries, extract_to_disk, pack_catalog, diff_file_sets |
| [Diff Patching](diff-patching) | generate_diff, validate_diff_file, validate_diff_directory |
| [Index Functions](index-functions) | build_index, open_index, is_index_stale, find_index_db, db_path_for_game_dir |
| [Discovery Functions](discovery-functions) | inspect_asset, search_assets, extract_macro |
| [Conflict Detection](conflict-detection) | check_conflicts |
| [Scaffolding Functions](scaffolding-functions) | scaffold_project, scaffold_ware, scaffold_equipment, scaffold_ship |
| [Translation Validation](translation-validation) | validate_translations, scaffold_translation |
| Schema Validation | validate_schema |
| Schema Extraction | extract_schema_to_db, extract_scriptproperties_to_db |
