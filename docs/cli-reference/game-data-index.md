---
title: "Game Data Index"
layout: default
parent: "CLI Reference"
nav_order: 3
---

# Game Data Index
## index

Build a SQLite index of game data (wares, macros, components, and their properties) for fast lookups.

```
x4cat index <game_dir> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `game_dir` | Path to X4 install directory |

**Options:**

| Option | Description |
|--------|-------------|
| `-o`, `--output PATH` | Output database path (default: `~/.cache/x4cat/<hash>.db`) |
| `--refresh` | Force rebuild even if the index is up to date |

**Examples:**

```bash
# Build the index (auto-detects if up to date)
x4cat index "/path/to/X4 Foundations"

# Force rebuild
x4cat index "/path/to/X4 Foundations" --refresh

# Store index at a custom path
x4cat index "/path/to/X4 Foundations" -o ./game_index.db
```

**Output:**

```
Indexed 8542 macros, 6231 components, 1847 wares -> /home/user/.cache/x4cat/a1b2c3d4.db
```

The index is automatically used by `inspect`, `search`, `extract-macro`, and `scaffold` commands. It detects when game `.cat` files have changed and skips rebuilding when already up to date.

---

## inspect

Look up a game asset by ware ID, macro name, or component name. Displays file paths, prices, owners, and macro properties.

```
x4cat inspect <asset_id> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `asset_id` | Ware ID, macro name, or component name |

**Options:**

| Option | Description |
|--------|-------------|
| `--db PATH` | Path to index database (default: auto-detect) |
| `--game-dir DIR` | Game directory (used to auto-build index if needed) |

**Examples:**

```bash
# Inspect a ware by ID
x4cat inspect energycells

# Inspect a ship macro
x4cat inspect ship_arg_s_fighter_01_a_macro

# Inspect with explicit game directory (auto-builds index)
x4cat inspect energycells --game-dir "/path/to/X4 Foundations"
```

**Sample output:**

```
ship_arg_s_fighter_01_a_macro (ship_s)
  Macro: assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
  Component: assets/units/size_s/ship_arg_s_fighter_01.xml
  Price: 67830 / 79800 / 91770  (min / avg / max)
  Owners: argon, antigone
  Properties:
    hull.max: 3200
    purpose.primary: fight
    ship.type: fighter
```

---

## search

Search game assets by partial match across IDs, groups, and tags.

```
x4cat search <term> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `term` | Search term (case-insensitive substring match) |

**Options:**

| Option | Description |
|--------|-------------|
| `--db PATH` | Path to index database (default: auto-detect) |
| `--game-dir DIR` | Game directory (used to auto-build index if needed) |
| `--type TYPE` | Filter results by type: `ware`, `macro`, or `component` |

**Examples:**

```bash
# Search for anything containing "fighter"
x4cat search fighter

# Search only wares
x4cat search energy --type ware

# Search macros related to Argon ships
x4cat search ship_arg --type macro
```

**Sample output:**

```
  macro       ship_arg_s_fighter_01_a_macro  (assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml)
  macro       ship_arg_s_fighter_01_b_macro  (assets/units/size_s/macros/ship_arg_s_fighter_01_b_macro.xml)
  ware        ship_arg_s_fighter_01_a  [ship] avg:79800

3 result(s)
```

---

## extract-macro

Extract a macro file by ID, resolving its virtual path through the index.

```
x4cat extract-macro <macro_id> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `macro_id` | Macro name (e.g., `ship_arg_s_fighter_01_a_macro`) |

**Options:**

| Option | Description |
|--------|-------------|
| `-o`, `--output DIR` | Output directory (default: current directory) |
| `--db PATH` | Path to index database (default: auto-detect) |
| `--game-dir DIR` | Game directory (default: read from index metadata) |

**Examples:**

```bash
# Extract a ship macro to the current directory
x4cat extract-macro ship_arg_s_fighter_01_a_macro

# Extract to a specific directory
x4cat extract-macro ship_arg_s_fighter_01_a_macro -o ./base/

# With explicit game directory
x4cat extract-macro shield_gen_m_standard_01_mk1_macro --game-dir "/path/to/X4 Foundations"
```

The file is written at its full virtual path under the output directory. For example:

```
./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
```

---
