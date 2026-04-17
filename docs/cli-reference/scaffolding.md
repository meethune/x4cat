---
title: "Scaffolding"
layout: default
parent: "CLI Reference"
nav_order: 4
---

# Scaffolding
## scaffold ware

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

## scaffold equipment

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

The index database is auto-detected from `~/.cache/x4cat/`. Use the global `--db` flag to specify a database: `x4cat --db path.db scaffold equipment ...`.

**Examples:**

```bash
# Clone a shield generator
x4cat scaffold equipment \
    --id shield_gen_m_custom_01_macro \
    --name "Custom Shield Mk1" \
    --clone-from shield_gen_m_standard_01_mk1_macro

# Clone a weapon with custom pricing
x4cat scaffold equipment \
    --id weapon_gen_m_laser_custom_macro \
    --name "Modded Pulse Laser" \
    --clone-from weapon_gen_m_laser_01_mk1_macro \
    --price-avg 25000

# With an explicit index database
x4cat --db ./game.db scaffold equipment \
    --id shield_gen_m_custom_01_macro \
    --name "Custom Shield Mk1" \
    --clone-from shield_gen_m_standard_01_mk1_macro
```

**Generated files:**

```
src/assets/props/.../macros/<macro_id>.xml   -- macro definition (cloned from source)
src/index/macros.xml                          -- diff patch registering the new macro
src/libraries/wares.xml                       -- diff patch adding the ware entry
src/t/0001-l044.xml                           -- English translation
```

---

## scaffold ship

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

The index database is auto-detected from `~/.cache/x4cat/`. Use the global `--db` flag to specify a database: `x4cat --db path.db scaffold ship ...`.

**Examples:**

```bash
# Clone an Argon fighter
x4cat scaffold ship \
    --id ship_my_s_fighter_01_a_macro \
    --name "Custom Fighter" \
    --clone-from ship_arg_s_fighter_01_a_macro \
    --size s \
    --price-avg 100000
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
Creating a truly new ship requires a 3D model and component XML. If you only want to **modify an existing ship's stats**, use the `extract-macro` + `xmldiff` workflow instead. See the [Modify Ship Stats tutorial](../tutorials/stat-mod).

---

## scaffold translation

Generate a translation stub for a new language from an existing translation file. Copies the page and entry structure with `[TRANSLATE: original text]` markers.

```
x4cat scaffold translation --from <source_file> --lang <code> -o <output_file>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--from FILE` | Source translation file (e.g., `t/0001-l044.xml`) |
| `--lang CODE` | Target language code (e.g., `49` for German, `33` for French) |
| `-o`, `--output FILE` | Output file path (required) |

**Language codes:** 44=English, 49=German, 33=French, 34=Spanish, 39=Italian, 42=Czech, 48=Polish, 55=Portuguese, 81=Japanese, 82=Korean, 86=Simplified Chinese, 88=Traditional Chinese.

**Example:**

```bash
# Generate a German translation stub from English
x4cat scaffold translation --from src/t/0001-l044.xml --lang 49 -o src/t/0001-l049.xml
```

---

## validate-translations

Validate that all `{pageId,entryId}` text references in mod XML files have matching entries in translation files.

```
x4cat validate-translations <mod_dir>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `mod_dir` | Mod directory to validate |

When an index database is available, `validate-translations` also performs collision detection against base game page IDs. Use the global `--db` flag for enhanced collision detection: `x4cat --db path.db validate-translations <mod_dir>`. The index database is auto-detected from `~/.cache/x4cat/` if available.

**Checks performed:**
- **MISSING** (error) — `{pageId,entryId}` referenced in mod XML but not defined in any `t/*.xml` file
- **ORPHAN** (warning) — entry defined in translation but never referenced in mod XML
- **Collision** (warning) — page ID below 90000 may conflict with base game
- **INCOMPLETE** (warning) — a language file is missing entries that exist in the English translation

Only mod-range page IDs (>= 90000) are checked. References to base game page IDs are ignored since they use the game's own translations.

**Example:**

```bash
x4cat validate-translations src/

# Output:
#   MISSING: {90001,10} referenced in mod XML but not defined in any translation file
#   ORPHAN: {90001,99} defined in translation but not referenced in mod XML
#   INCOMPLETE: language 49, page 90001 missing entries: [2, 3]
#
#   1 error(s), 2 warning(s)
```

---

## init

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
