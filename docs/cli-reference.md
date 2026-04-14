---
title: CLI Reference
layout: default
nav_order: 3
---

# CLI Reference

All commands follow the pattern:

```
x4cat <command> [arguments] [options]
```

Use `x4cat <command> --help` for built-in help on any subcommand.

---

## Archive Operations

### list (alias: ls)

List files inside `.cat/.dat` archives.

```
x4cat list <game_dir> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `game_dir` | Path to X4 install directory or extension directory |

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

### extract (alias: x)

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

### pack

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

### diff

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

## XML Diff Patching

### xmldiff

Generate an X4-compatible XML diff patch from a base file and a modified copy.

```
x4cat xmldiff --base <base.xml> --mod <modified.xml> [-o <output.xml>]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--base FILE` | Base/original XML file (required) |
| `--mod FILE` | Modified XML file (required) |
| `-o`, `--output FILE` | Output diff patch file. If omitted, prints to stdout. |

**Examples:**

```bash
# Generate a diff patch and write to file
x4cat xmldiff --base ./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
              --mod  ./modified/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
              -o src/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml

# Print diff patch to stdout
x4cat xmldiff --base original.xml --mod changed.xml
```

The generated diff uses `<add>`, `<replace>`, and `<remove>` operations with XPath selectors, following the X4 diff patch format.

---

### validate-diff

Validate XML diff patches against base game files. Checks that every `sel` XPath in each diff operation matches at least one element in the base game XML.

```
x4cat validate-diff <game_dir> <mod_dir> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `game_dir` | Path to X4 install directory |
| `mod_dir` | Directory containing diff patch XML files |

**Options:**

| Option | Description |
|--------|-------------|
| `-p`, `--prefix PREFIX` | Catalog filename prefix for game files |
| `--strict` | Treat unsupported XPath warnings as errors (exit code 1) |

**Examples:**

```bash
# Validate all diff patches in src/ against the base game
x4cat validate-diff "/path/to/X4 Foundations" ./src

# Strict mode: fail on any warning
x4cat validate-diff "/path/to/X4 Foundations" ./src --strict
```

**Output format:**

```
libraries/wares.xml:3: PASS  sel="/wares"  (root element matched)
libraries/wares.xml:4: PASS  sel="/wares/ware[@id='energycells']/price/@max"  (1 element(s) matched)
libraries/wares.xml:7: FAIL  sel="/wares/ware[@id='doesnotexist']"  (no elements matched: ware[@id='doesnotexist'])

1 file(s), 3 operation(s): 2 passed, 1 failed, 0 warning(s), 0 skipped
```

Exit code is 0 if all operations pass, 1 if any fail (or if `--strict` is set and there are warnings).

---

## Game Data Index

### index

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

### inspect

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

### search

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

### extract-macro

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

## Scaffolding

### scaffold ware

Generate boilerplate for a new trade ware. Creates a `libraries/wares.xml` diff patch and a translation file.

```
x4cat scaffold ware --id <ware_id> --name <display_name> [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--id ID` | Ware ID (required) |
| `--name NAME` | Display name (required) |
| `--description TEXT` | Ware description |
| `--group GROUP` | Ware group (e.g., `hightech`, `energy`, `pharmaceutical`) |
| `--volume N` | Volume per unit (default: 1) |
| `--price-min N` | Minimum price |
| `--price-avg N` | Average price (auto-derives min/max if they are 0) |
| `--price-max N` | Maximum price |
| `-o`, `--output DIR` | Output directory (default: `./src`) |

**Examples:**

```bash
# Scaffold a basic ware
x4cat scaffold ware --id quantum_tubes --name "Quantum Tubes" \
    --group hightech --price-avg 5000 --volume 10

# With full pricing and description
x4cat scaffold ware --id quantum_tubes --name "Quantum Tubes" \
    --description "High-energy containment tubes for quantum devices" \
    --group hightech --volume 10 \
    --price-min 4000 --price-avg 5000 --price-max 6000 \
    -o ./src
```

**Generated files:**

```
src/libraries/wares.xml     -- diff patch adding the ware
src/t/0001-l044.xml         -- English translation
```

---

### scaffold equipment

Clone an existing equipment item (engine, weapon, shield, etc.) and generate all required files including macro, index registration, ware entry, and translations.

```
x4cat scaffold equipment --id <macro_id> --name <name> --clone-from <source_macro> [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--id ID` | New macro ID (required) |
| `--name NAME` | Display name (required) |
| `--clone-from MACRO` | Macro ID of existing equipment to clone (required) |
| `--description TEXT` | Description |
| `--price-min N` | Minimum price (defaults to source price) |
| `--price-avg N` | Average price |
| `--price-max N` | Maximum price |
| `-o`, `--output DIR` | Output directory (default: `./src`) |
| `--db PATH` | Index database path |
| `--game-dir DIR` | Game directory (auto-builds index if needed) |

**Examples:**

```bash
# Clone a shield generator
x4cat scaffold equipment \
    --id shield_gen_m_custom_01_macro \
    --name "Custom Shield Mk1" \
    --clone-from shield_gen_m_standard_01_mk1_macro \
    --game-dir "/path/to/X4 Foundations"

# Clone a weapon with custom pricing
x4cat scaffold equipment \
    --id weapon_gen_m_laser_custom_macro \
    --name "Modded Pulse Laser" \
    --clone-from weapon_gen_m_laser_01_mk1_macro \
    --price-avg 25000 \
    --game-dir "/path/to/X4 Foundations"
```

**Generated files:**

```
src/assets/props/.../macros/<macro_id>.xml   -- macro definition (cloned from source)
src/index/macros.xml                          -- diff patch registering the new macro
src/libraries/wares.xml                       -- diff patch adding the ware entry
src/t/0001-l044.xml                           -- English translation
```

---

### scaffold ship

Clone an existing ship macro to create a new ship. Generates macro, index registration (macros + components), ware entry, and translations.

```
x4cat scaffold ship --id <macro_id> --name <name> --clone-from <source_macro> [options]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--id ID` | New macro ID (required) |
| `--name NAME` | Display name (required) |
| `--clone-from MACRO` | Ship macro ID to clone (required) |
| `--size SIZE` | Ship size class: `s`, `m`, `l`, or `xl` (default: `s`) |
| `--description TEXT` | Description |
| `--price-min N` | Minimum price |
| `--price-avg N` | Average price |
| `--price-max N` | Maximum price |
| `-o`, `--output DIR` | Output directory (default: `./src`) |
| `--db PATH` | Index database path |
| `--game-dir DIR` | Game directory |

**Examples:**

```bash
# Clone an Argon fighter
x4cat scaffold ship \
    --id ship_my_s_fighter_01_a_macro \
    --name "Custom Fighter" \
    --clone-from ship_arg_s_fighter_01_a_macro \
    --size s \
    --price-avg 100000 \
    --game-dir "/path/to/X4 Foundations"
```

**Generated files:**

```
src/assets/units/size_s/macros/<macro_id>.xml   -- ship macro
src/index/macros.xml                             -- macro index diff
src/index/components.xml                         -- component index diff
src/libraries/wares.xml                          -- ware entry diff
src/t/0001-l044.xml                              -- English translation
README_SHIP.md                                   -- notes on what else you need
```

{: .important }
Creating a truly new ship requires a 3D model and component XML. If you only want to **modify an existing ship's stats**, use the `extract-macro` + `xmldiff` workflow instead. See the [Modify Ship Stats tutorial](tutorials/stat-mod).

---

### init

Scaffold a complete mod project from the [extension_poc](https://github.com/meethune/extension_poc) template. Creates a ready-to-build project with `content.xml`, `Makefile`, tests, and directory structure.

```
x4cat init <mod_id> [options]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `mod_id` | Mod identifier (e.g., `my_awesome_mod`). Must start with a letter, contain only alphanumeric characters and underscores, max 64 characters. |

**Options:**

| Option | Description |
|--------|-------------|
| `-o`, `--output DIR` | Output directory (default: `./<mod_id>`) |
| `--author NAME` | Author name (default: from `git config user.name`) |
| `--description TEXT` | Mod description |
| `--game-version N` | Minimum game version as integer (default: `900` for v9.00) |
| `--repo URL` | Repository URL or GitHub shorthand (e.g., `user/repo`) |
| `--git` | Initialize a git repository in the project |

**Examples:**

```bash
# Basic project scaffold
x4cat init my_balance_mod

# Full options
x4cat init my_balance_mod \
    --author "Your Name" \
    --description "Ship balance adjustments" \
    --game-version 900 \
    --repo myuser/my_balance_mod \
    --git

# Custom output directory
x4cat init my_mod -o /home/user/mods/my_mod --git
```

**Generated project structure:**

```
my_balance_mod/
  content.xml          -- extension manifest
  Makefile             -- build, validate, test, clean targets
  pyproject.toml       -- uv project with x4cat dependency
  README.md
  .gitignore
  src/
    md/                -- Mission Director scripts
    aiscripts/         -- AI scripts
    libraries/         -- library diff patches
  tests/
    __init__.py
    test_mod.py        -- XML validation tests
```

**Make targets in the generated project:**

```bash
make all                    # validate + build + test
make build                  # pack src/ into dist/ext_01.cat
make validate               # run structural XML validation
make lint X4_GAME_DIR=...   # validate diff patches against game
make test                   # run pytest
make clean                  # remove dist/
```
