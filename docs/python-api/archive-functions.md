---
title: "Archive Functions"
layout: default
parent: "Python API"
nav_order: 2
---

# Archive Functions
## build_vfs

Build a virtual filesystem from all matching catalogs in a directory. Later catalogs override earlier ones for the same path, matching X4's load order.

```python
from x4_catalog import build_vfs

vfs = build_vfs(Path("/path/to/X4 Foundations"))
# vfs is dict[str, CatEntry]

entry = vfs.get("libraries/wares.xml")
if entry:
    print(f"wares.xml is {entry.size} bytes, in {entry.cat_path}")
```

**Signature:**

```python
def build_vfs(directory: Path, prefix: str = "") -> dict[str, CatEntry]: ...
```

| Parameter | Description |
|-----------|-------------|
| `directory` | Path to game install or extension directory |
| `prefix` | Catalog filename prefix (`""` for `NN.cat`, `"ext_"` for `ext_NN.cat`) |

## build_vfs_multi

Build a merged VFS from multiple source directories. Later sources override earlier ones.

```python
from x4_catalog import build_vfs_multi

vfs = build_vfs_multi([
    (Path("/path/to/X4 Foundations"), ""),
    (Path("/path/to/X4 Foundations/extensions/ego_dlc_boron"), "ext_"),
])
```

**Signature:**

```python
def build_vfs_multi(sources: list[tuple[Path, str]]) -> dict[str, CatEntry]: ...
```

## list_entries

Return deduplicated catalog entries, optionally filtered by glob and regex patterns.

```python
from x4_catalog import list_entries

# List all MD scripts
entries = list_entries(Path("/path/to/X4 Foundations"), glob_pattern="md/*.xml")
for entry in entries:
    print(f"{entry.size:>10}  {entry.path}")
```

**Signature:**

```python
def list_entries(
    directory: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
    include_re: str | None = None,
    exclude_re: str | None = None,
) -> list[CatEntry]: ...
```

## extract_to_disk

Extract files to disk, preserving directory structure and modification times. Verifies MD5 checksums during extraction.

```python
from x4_catalog import extract_to_disk

written = extract_to_disk(
    Path("/path/to/X4 Foundations"),
    Path("./unpacked"),
    glob_pattern="libraries/wares.xml",
)
print(f"Extracted {len(written)} file(s)")
```

**Signature:**

```python
def extract_to_disk(
    directory: Path,
    output_dir: Path,
    glob_pattern: str | None = None,
    prefix: str = "",
    include_re: str | None = None,
    exclude_re: str | None = None,
) -> list[Path]: ...
```

Returns a list of written file paths.

## pack_catalog

Pack loose files from a directory into a `.cat/.dat` pair.

```python
from x4_catalog import pack_catalog

count = pack_catalog(Path("./src"), Path("./dist/ext_01.cat"))
print(f"Packed {count} files")

# Append to an existing catalog
pack_catalog(Path("./extra"), Path("./dist/ext_01.cat"), append=True)
```

**Signature:**

```python
def pack_catalog(source_dir: Path, cat_path: Path, append: bool = False) -> int: ...
```

Returns the number of files packed.

## iter_cat_files

Return `.cat` files matching `{prefix}NN.cat` sorted by numeric ID. Signature catalogs (`*_sig.cat`) are excluded.

```python
from x4_catalog import iter_cat_files

cats = iter_cat_files(Path("/path/to/X4 Foundations"))
# [Path('01.cat'), Path('02.cat'), ...]
```

**Signature:**

```python
def iter_cat_files(directory: Path, prefix: str = "") -> list[Path]: ...
```

## parse_cat_line

Parse a single `.cat` index line into a `CatEntry`. The `cat_path` and `dat_offset` fields are set to placeholders -- this function is useful for parsing individual lines without full catalog context.

```python
from x4_catalog import parse_cat_line

entry = parse_cat_line("libraries/wares.xml 790216 1775564527 1df31b1302a8db514139e40d6f975f30")
print(entry.path, entry.size, entry.md5)
```

**Signature:**

```python
def parse_cat_line(line: str) -> CatEntry: ...
```

Raises `ValueError` on blank lines, malformed fields, negative sizes, or invalid MD5 hashes.

## read_payload

Read the raw bytes for a single `CatEntry` from its `.dat` file, with MD5 integrity verification.

```python
from x4_catalog import read_payload, build_vfs
from pathlib import Path

vfs = build_vfs(Path("/path/to/X4 Foundations"))
data = read_payload(vfs["libraries/wares.xml"])
```

```python
def read_payload(entry: CatEntry) -> bytes: ...
```

Raises `OSError` on short reads or MD5 mismatches.

---

## diff_and_pack

Compare two directories and pack changed files into a catalog.

```python
from x4_catalog import diff_and_pack

changed, deleted = diff_and_pack(
    Path("./original"),
    Path("./modified"),
    Path("./dist/ext_01.cat"),
)
print(f"{changed} changed, {deleted} deleted")
```

**Signature:**

```python
def diff_and_pack(base_dir: Path, mod_dir: Path, cat_path: Path) -> tuple[int, int]: ...
```

Returns `(num_changed, num_deleted)`.

## diff_file_sets

Compare two directories and identify changes without packing.

```python
from x4_catalog import diff_file_sets

changed, deleted = diff_file_sets(Path("./original"), Path("./modified"))
for vpath, disk_path in changed.items():
    print(f"Changed: {vpath}")
for vpath in deleted:
    print(f"Deleted: {vpath}")
```

**Signature:**

```python
def diff_file_sets(
    base_dir: Path, mod_dir: Path
) -> tuple[dict[str, Path], list[str]]: ...
```

Returns `(changed, deleted)` where `changed` maps virtual paths to disk paths and `deleted` is a list of virtual paths present in base but absent in mod.

---
