---
title: "Translation Validation"
layout: default
parent: "Python API"
nav_order: 8
---

# Translation Validation
## validate_translations

```python
from x4_catalog import validate_translations

result = validate_translations(Path("./src"))
# result["errors"]   -- list of missing translation errors
# result["warnings"] -- list of orphan/collision/incomplete warnings
```

```python
def validate_translations(
    mod_dir: Path,
    db_path: Path | str | None = None,
) -> ValidationReport: ...
```

When `db_path` is provided, collision detection against base game translation page IDs is enabled.

Scans all XML files in `mod_dir` for `{pageId,entryId}` references and cross-checks against `t/*.xml` translation files. Only mod-range page IDs (>= 90000) are validated; base game references are ignored.

## scaffold_translation

```python
from x4_catalog import scaffold_translation

scaffold_translation(
    Path("src/t/0001-l044.xml"),
    Path("src/t/0001-l049.xml"),
    lang_code=49,
)
```

```python
def scaffold_translation(
    source_path: Path,
    output_path: Path,
    *,
    lang_code: int,
) -> None: ...
```

Generates a translation stub for a new language, copying the page/entry structure with `[TRANSLATE: original text]` markers.
