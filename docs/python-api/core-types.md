---
title: "Core Types"
layout: default
parent: "Python API"
nav_order: 1
---

# Core Types
## CatEntry

A single entry from a `.cat` index file.

```python
from x4_catalog import CatEntry
```

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | Virtual path (forward slashes, no leading slash) |
| `size` | `int` | File size in bytes |
| `mtime` | `int` | Unix timestamp (seconds since epoch) |
| `md5` | `str` | MD5 hex digest (32 characters) |
| `cat_path` | `Path` | Path to the `.cat` file containing this entry |
| `dat_offset` | `int` | Byte offset into the corresponding `.dat` file |

`CatEntry` is a frozen dataclass (immutable and hashable).

## DiffOp

A single operation parsed from a diff patch file.

```python
from x4_catalog import DiffOp
```

| Field | Type | Description |
|-------|------|-------------|
| `tag` | `str` | Operation type: `"add"`, `"replace"`, or `"remove"` |
| `sel` | `str` | XPath selector |
| `pos` | `str` | Position attribute (e.g., `"before"`, `"after"`) |
| `type_attr` | `str` | Type attribute (e.g., `"@newtag"` for adding attributes) |
| `if_cond` | `str` | Conditional XPath (empty string if unconditional) |
| `line` | `int` | Line number in the source file |

## ValidationResult

Result of validating one diff operation against base game XML.

```python
from x4_catalog import ValidationResult
```

| Field | Type | Description |
|-------|------|-------------|
| `op` | `DiffOp` | The operation that was validated |
| `sel_matched` | `bool` | Whether the `sel` XPath matched |
| `if_matched` | `bool \| None` | Whether the `if` condition matched (`None` if no condition) |
| `sel_detail` | `str` | Human-readable description of the match result |
| `if_detail` | `str` | Human-readable description of the condition result |

## FileValidationReport

Validation results for one diff patch file.

```python
from x4_catalog import FileValidationReport
```

| Field | Type | Description |
|-------|------|-------------|
| `diff_file` | `Path` | Path to the diff patch file |
| `virtual_path` | `str` | Virtual path (e.g., `libraries/wares.xml`) |
| `base_found` | `bool` | Whether the corresponding base game file was found |
| `parse_error` | `str \| None` | Parse error message, or `None` if parsing succeeded |
| `results` | `list[ValidationResult]` | Per-operation validation results |

## ValidationReport

Return type for validation functions (`validate_translations`, `validate_schema`). A `TypedDict`.

```python
from x4_catalog import ValidationReport
```

| Field | Type | Description |
|-------|------|-------------|
| `errors` | `list[str]` | List of error messages |
| `warnings` | `list[str]` | List of warning messages |

## ConflictEntry

A single conflict or overlap between mods. A `TypedDict`.

```python
from x4_catalog import ConflictEntry
```

| Field | Type | Description |
|-------|------|-------------|
| `file` | `str` | Virtual path of the conflicting file |
| `sel` | `str` | XPath selector |
| `mods` | `list[str]` | Names of the mods involved |
| `operations` | `dict[str, list[str]]` | Operations per mod |

## ConflictReport

Return type for `check_conflicts()`. A `TypedDict`.

```python
from x4_catalog import ConflictReport
```

| Field | Type | Description |
|-------|------|-------------|
| `conflicts` | `list[ConflictEntry]` | Conflicting overlaps (replace+replace, remove+add/replace) |
| `safe` | `list[ConflictEntry]` | Safe overlaps (add+add) |
| `info` | `list[ConflictEntry]` | Mixed operations that may interact |
| `files_checked` | `int` | Number of shared files checked |

---
