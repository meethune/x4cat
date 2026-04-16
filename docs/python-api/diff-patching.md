---
title: "Diff Patching Functions"
layout: default
parent: "Python API"
nav_order: 3
---

# Diff Patching Functions
## generate_diff

Generate an X4-compatible XML diff patch from two XML files.

```python
from x4_catalog import generate_diff

base_data = Path("base/libraries/wares.xml").read_bytes()
mod_data = Path("modified/libraries/wares.xml").read_bytes()

diff_bytes = generate_diff(base_data, mod_data)
Path("src/libraries/wares.xml").write_bytes(diff_bytes)
```

**Signature:**

```python
def generate_diff(base_data: bytes, mod_data: bytes) -> bytes: ...
```

Returns the diff XML as bytes. Raises `ValueError` if the root elements have different tag names.

## validate_diff_file

Validate a single diff patch against its base game XML.

```python
from x4_catalog import validate_diff_file

report = validate_diff_file(
    diff_data=Path("src/libraries/wares.xml").read_bytes(),
    base_data=base_wares_bytes,
    diff_path=Path("src/libraries/wares.xml"),
    virtual_path="libraries/wares.xml",
)
for result in report.results:
    status = "PASS" if result.sel_matched else "FAIL"
    print(f"{status}: {result.op.sel}")
```

**Signature:**

```python
def validate_diff_file(
    diff_data: bytes,
    base_data: bytes,
    diff_path: Path,
    virtual_path: str,
) -> FileValidationReport: ...
```

## validate_diff_directory

Validate all diff patches in a directory against base game files. Non-diff XML files are silently skipped.

```python
from x4_catalog import validate_diff_directory

reports = validate_diff_directory(
    Path("/path/to/X4 Foundations"),
    Path("./src"),
)
for report in reports:
    for r in report.results:
        if not r.sel_matched:
            print(f"FAIL: {report.virtual_path} sel={r.op.sel}")
```

**Signature:**

```python
def validate_diff_directory(
    game_dir: Path,
    mod_dir: Path,
    prefix: str = "",
) -> list[FileValidationReport]: ...
```

---
