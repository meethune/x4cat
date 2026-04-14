---
title: Python API
layout: default
nav_order: 4
---

# Python API Reference

x4cat can be used as a Python library for building custom tooling, automation scripts, or integration into larger modding pipelines.

```python
import x4_catalog
```

All public symbols are exported from the top-level `x4_catalog` package.

---

## Core Types

### CatEntry

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

### DiffOp

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

### ValidationResult

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

### FileValidationReport

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

---

## Archive Functions

### build_vfs

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

### build_vfs_multi

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

### list_entries

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

### extract_to_disk

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

### pack_catalog

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

### iter_cat_files

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

### parse_cat_line

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

### diff_and_pack

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

### diff_file_sets

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

## Diff Patching Functions

### generate_diff

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

### validate_diff_file

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

### validate_diff_directory

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

## Index Functions

### build_index

Build a SQLite index from game files. Indexes macros, components, wares, and macro properties.

```python
from x4_catalog import build_index

db_path = build_index(Path("/path/to/X4 Foundations"), Path("./game.db"))
```

**Signature:**

```python
def build_index(game_dir: Path, db_path: Path) -> Path: ...
```

Overwrites any existing database at `db_path`. Returns the path to the created database.

### open_index

Open an existing index database with `row_factory` set to `sqlite3.Row`.

```python
from x4_catalog import open_index

conn = open_index(Path("./game.db"))
row = conn.execute("SELECT * FROM wares WHERE ware_id = ?", ("energycells",)).fetchone()
print(dict(row))
conn.close()
```

**Signature:**

```python
def open_index(db_path: Path) -> sqlite3.Connection: ...
```

Raises `FileNotFoundError` if the database does not exist.

### is_index_stale

Check if an index is stale relative to the game's `.cat` files.

```python
from x4_catalog import is_index_stale

if is_index_stale(Path("/path/to/X4 Foundations"), Path("./game.db")):
    build_index(Path("/path/to/X4 Foundations"), Path("./game.db"))
```

**Signature:**

```python
def is_index_stale(game_dir: Path, db_path: Path) -> bool: ...
```

### find_index_db

Find an existing index database in the default cache directory (`~/.cache/x4cat/`). Returns the most recently modified `.db` file.

```python
from x4_catalog import find_index_db

db = find_index_db()
if db is not None:
    print(f"Found index at {db}")
```

**Signature:**

```python
def find_index_db() -> Path | None: ...
```

### db_path_for_game_dir

Return the default database path for a given game directory. Uses a SHA-256 hash of the resolved path.

```python
from x4_catalog import db_path_for_game_dir

db = db_path_for_game_dir(Path("/path/to/X4 Foundations"))
# Path('/home/user/.cache/x4cat/a1b2c3d4e5f6g7h8.db')
```

**Signature:**

```python
def db_path_for_game_dir(game_dir: Path) -> Path: ...
```

---

## Discovery Functions

### inspect_asset

Look up an asset by ware ID, macro name, or component name. Tries ware first, then macro, then component.

```python
from x4_catalog import inspect_asset

result = inspect_asset("energycells", Path("./game.db"))
if result:
    print(result["ware_id"], result["price_avg"])
```

**Signature:**

```python
def inspect_asset(asset_id: str, db_path: Any) -> dict[str, Any] | None: ...
```

Returns a dict with all known information or `None` if not found.

### search_assets

Search across wares, macros, and components by case-insensitive substring match.

```python
from x4_catalog import search_assets

results = search_assets("fighter", Path("./game.db"), type_filter="macro")
for r in results:
    print(f"{r['type']:10s} {r['id']}")
```

**Signature:**

```python
def search_assets(
    term: str,
    db_path: Any,
    *,
    type_filter: str | None = None,
) -> list[dict[str, str]]: ...
```

Each result dict has keys: `id`, `type`, `path`, `detail`.

### extract_macro

Extract a macro file by ID, resolving its virtual path through the index.

```python
from x4_catalog import extract_macro

result = extract_macro(
    "ship_arg_s_fighter_01_a_macro",
    Path("./game.db"),
    Path("/path/to/X4 Foundations"),
    Path("./output"),
)
if result:
    print(f"Extracted to {result}")
```

**Signature:**

```python
def extract_macro(
    macro_id: str,
    db_path: Any,
    game_dir: Path,
    output_dir: Path,
) -> Path | None: ...
```

Returns the path to the extracted file, or `None` if the macro is not found.

---

## Scaffolding Functions

### scaffold_project

Create a new mod project from the extension_poc template.

```python
from x4_catalog import scaffold_project

project_dir = scaffold_project(
    "my_mod",
    author="Your Name",
    description="A custom X4 mod",
    game_version=900,
    repo="youruser/my_mod",
    init_git=True,
)
print(f"Created project at {project_dir}")
```

**Signature:**

```python
def scaffold_project(
    mod_id: str,
    *,
    output_dir: Path | None = None,
    author: str | None = None,
    description: str | None = None,
    game_version: int = 900,
    repo: str | None = None,
    init_git: bool = False,
) -> Path: ...
```

Returns the path to the created project directory. Raises `FileExistsError` if the output directory already exists and is non-empty. Raises `ValueError` if `mod_id` is invalid.

### scaffold_ware

Generate boilerplate for a trade ware (Tier 1 -- no macro needed).

```python
from x4_catalog import scaffold_ware

files = scaffold_ware(
    "quantum_tubes",
    "Quantum Tubes",
    Path("./src"),
    group="hightech",
    price_avg=5000,
    volume=10,
)
# files = ["libraries/wares.xml", "t/0001-l044.xml"]
```

**Signature:**

```python
def scaffold_ware(
    ware_id: str,
    name: str,
    output_dir: Path,
    *,
    description: str = "",
    group: str = "",
    transport: str = "container",
    volume: int = 1,
    tags: str = "container economy",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

Returns a list of generated file paths relative to `output_dir`.

### scaffold_equipment

Clone an existing equipment item and generate all required files (Tier 2).

```python
from x4_catalog import scaffold_equipment

files = scaffold_equipment(
    "shield_gen_m_custom_01_macro",
    "Custom Shield",
    Path("./src"),
    clone_from="shield_gen_m_standard_01_mk1_macro",
    db_path=Path("./game.db"),
)
```

**Signature:**

```python
def scaffold_equipment(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Any = None,
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

### scaffold_ship

Clone an existing ship macro to create a new ship (Tier 3).

```python
from x4_catalog import scaffold_ship

files = scaffold_ship(
    "ship_my_s_fighter_01_a_macro",
    "Custom Fighter",
    Path("./src"),
    clone_from="ship_arg_s_fighter_01_a_macro",
    db_path=Path("./game.db"),
    size="s",
    price_avg=100000,
)
```

**Signature:**

```python
def scaffold_ship(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Any = None,
    size: str = "s",
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

Returns a list of generated file paths relative to `output_dir`. Note that creating a new ship also requires a component XML and 3D model -- see the generated `README_SHIP.md` for details.
