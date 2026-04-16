---
title: "Archive Operations"
layout: default
parent: "CLI Reference"
nav_order: 1
---

# Archive Operations
## list (alias: ls)

List files inside `.cat/.dat` archives. Can operate from either VFS (direct catalog scan) or the SQLite index.

```
x4cat list <game_dir> [options]      # from VFS
x4cat --db game.db list [options]    # from index
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `game_dir` | Path to X4 install directory (optional if `--db` is provided) |

**Options:**

| Option | Description |
|--------|-------------|
| `-g`, `--glob PATTERN` | Filter by glob pattern (e.g., `md/*.xml`) |
| `--include REGEX` | Include only paths matching this regex |
| `--exclude REGEX` | Exclude paths matching this regex |
| `-p`, `--prefix PREFIX` | Catalog filename prefix (default: `""` for base game `NN.cat`; use `ext_` for extension catalogs) |

**Examples:**

```bash
# List all files in the base game
x4cat list "/path/to/X4 Foundations"

# List only Mission Director scripts
x4cat list "/path/to/X4 Foundations" -g 'md/*.xml'

# List libraries, excluding XSD schemas
x4cat list "/path/to/X4 Foundations" --include '^libraries/' --exclude '\.xsd$'

# List files inside a DLC extension
x4cat list "/path/to/X4 Foundations/extensions/ego_dlc_boron" -p ext_
```

**Output format:**

```
       12345  libraries/wares.xml
        5678  md/setup.xml
         ...

42 file(s)
```

Each line shows file size (in bytes, right-aligned) followed by the virtual path.

---

## extract (alias: x)

Extract files from `.cat/.dat` archives to disk. Preserves directory structure and file timestamps.

```
x4cat extract <game_dir> -o <output_dir> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `game_dir` | Path to X4 install directory or extension directory |

**Options:**

| Option | Description |
|--------|-------------|
| `-o`, `--output DIR` | Output directory (required) |
| `-g`, `--glob PATTERN` | Filter by glob pattern |
| `--include REGEX` | Include only paths matching this regex |
| `--exclude REGEX` | Exclude paths matching this regex |
| `-p`, `--prefix PREFIX` | Catalog filename prefix |

**Examples:**

```bash
# Extract all XML library files
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'libraries/*.xml'

# Extract a single file
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'libraries/wares.xml'

# Extract XSD schemas for validation
x4cat extract "/path/to/X4 Foundations" -o ./schemas -g '*.xsd'

# Extract all files from the Boron DLC
x4cat extract "/path/to/X4 Foundations/extensions/ego_dlc_boron" -o ./boron -p ext_

# Extract AI scripts only
x4cat extract "/path/to/X4 Foundations" -o ./unpacked --include '^aiscripts/'
```

---

## pack

Pack loose files from a directory into a `.cat/.dat` catalog pair.

```
x4cat pack <source_dir> -o <output.cat> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `source_dir` | Directory of loose files to pack |

**Options:**

| Option | Description |
|--------|-------------|
| `-o`, `--output PATH` | Output `.cat` file path (required). The `.dat` file is created alongside it. |
| `--append` | Append to an existing catalog instead of overwriting |

**Examples:**

```bash
# Pack mod source files into ext_01.cat/dat
x4cat pack ./src -o ./dist/ext_01.cat

# Append additional files to an existing catalog
x4cat pack ./extra -o ./dist/ext_01.cat --append
```

The directory structure under `source_dir` becomes the virtual path inside the catalog. For example, `./src/libraries/wares.xml` is packed as `libraries/wares.xml`.

---

## diff

Compare two directories and pack only new or changed files into a catalog.

```
x4cat diff --base <base_dir> --mod <mod_dir> -o <output.cat>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--base DIR` | Base/original directory (required) |
| `--mod DIR` | Modified directory (required) |
| `-o`, `--output PATH` | Output `.cat` file path (required) |

**Examples:**

```bash
# Generate a diff catalog from base and modified directories
x4cat diff --base ./original --mod ./modified -o ./dist/ext_01.cat
```

**Output:**

```
3 changed/added, 1 deleted

Deleted files (not in catalog -- handle via XML diff patches):
  - libraries/removed_file.xml

Diff catalog written to ./dist/ext_01.cat
```

Deleted files are reported but not embedded in the catalog. X4 does not support deletion markers in extension catalogs -- use XML diff patches with `<remove>` operations instead.

---
