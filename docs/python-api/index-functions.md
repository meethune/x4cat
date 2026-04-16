---
title: "Index Functions"
layout: default
parent: "Python API"
nav_order: 4
---

# Index Functions
## build_index

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

## open_index

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

## is_index_stale

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

## find_index_db

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

## db_path_for_game_dir

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
