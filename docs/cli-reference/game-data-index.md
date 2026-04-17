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
Indexed 8542 macros, 6231 components, 1847 wares, 12450 files
  + 320 schema rules, 4500 script properties
  → /home/user/.cache/x4cat/a1b2c3d4.db
```

The index is automatically used by `inspect`, `search`, `extract-macro`, `scaffold`, `validate-schema`, and `validate-translations` commands. It detects when game `.cat` files have changed and skips rebuilding when already up to date.

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

The index database is auto-detected from `~/.cache/x4cat/`. Use `x4cat --db <path>` to specify explicitly.

**Examples:**

```bash
# Inspect a ware by ID
x4cat inspect energycells

# Inspect a ship macro
x4cat inspect ship_arg_s_fighter_01_a_macro

# With an explicit index database
x4cat --db ./game.db inspect energycells
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

Search game assets by partial match across IDs, names, groups, and tags. Wares are also searchable by their resolved English name (e.g., "Energy Cells").

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
| `--type TYPE` | Filter results by type: `ware`, `macro`, `component`, `datatype`, or `keyword` |

The index database is auto-detected from `~/.cache/x4cat/`. Use `x4cat --db <path>` to specify explicitly.

**Examples:**

```bash
# Search for anything containing "fighter"
x4cat search fighter

# Search by in-game name
x4cat search "Energy Cells"

# Search only wares
x4cat search energy --type ware

# Search macros related to Argon ships
x4cat search ship_arg --type macro

# Search script datatypes
x4cat search ship --type datatype

# With an explicit index database
x4cat --db ./game.db search fighter
```

**Sample output:**

```
  ware        energycells  — Energy Cells [energy] avg:16

1 result(s)
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

The index database is auto-detected from `~/.cache/x4cat/`. Use `x4cat --db <path>` to specify explicitly. The game directory is read from the index metadata.

**Examples:**

```bash
# Extract a ship macro to the current directory
x4cat extract-macro ship_arg_s_fighter_01_a_macro

# Extract to a specific directory
x4cat extract-macro ship_arg_s_fighter_01_a_macro -o ./base/

# With an explicit index database
x4cat --db ./game.db extract-macro shield_gen_m_standard_01_mk1_macro
```

The file is written at its full virtual path under the output directory. For example:

```
./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
```

---
