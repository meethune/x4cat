---
title: Set Up a Mod Project
layout: default
parent: Tutorials
---

# Set Up a Mod Project

The `x4cat init` command scaffolds a complete mod project with a `Makefile`, tests, and directory structure based on the [extension_poc](https://github.com/meethune/extension_poc) template. This gives you a repeatable build pipeline for developing, validating, and distributing your mod.

## What you will build

A fully structured mod project with:

- `content.xml` extension manifest
- `Makefile` with build, validate, lint, and test targets
- `pyproject.toml` for dependency management via uv
- Automated XML validation tests
- Standard directory layout matching X4 conventions

## Step 1: Scaffold the project

```bash
x4cat init my_balance_mod \
    --author "Your Name" \
    --description "Ship and weapon balance adjustments for X4" \
    --game-version 900 \
    --repo youruser/my_balance_mod \
    --git
```

This creates:

```
my_balance_mod/
  content.xml
  Makefile
  pyproject.toml
  README.md
  .gitignore
  src/
    md/
      my_balance_mod.xml    -- starter MD script
    aiscripts/
    libraries/
  tests/
    __init__.py
    test_mod.py
```

## Step 2: Understand the project structure

### content.xml

The extension manifest that X4 reads to load your mod:

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="my_balance_mod"
         version="100"
         name="my_balance_mod"
         description="Ship and weapon balance adjustments for X4"
         author="Your Name"
         date="2026-04-13"
         enabled="1"
         save="0">
  <dependency version="900" />
</content>
```

Edit the `name` to something human-friendly, and set `save="1"` if your mod affects gameplay/save data.

### src/ directory

All mod content goes here. This directory is packed into `ext_01.cat/dat` during build. The directory structure mirrors X4's virtual filesystem:

```
src/
  md/                  -- Mission Director scripts
  aiscripts/           -- AI scripts
  libraries/           -- diff patches for game data XML
  t/                   -- translation files
  index/               -- macro/component index diffs
  assets/              -- macro files for new content
```

### Makefile

The Makefile provides standard targets:

| Target | Command | Description |
|--------|---------|-------------|
| `all` | `make all` | validate + build + test |
| `build` | `make build` | Pack `src/` into `dist/ext_01.cat` |
| `validate` | `make validate` | Run structural XML validation (pytest) |
| `lint` | `make lint X4_GAME_DIR=...` | Validate diff patches against game files |
| `schemas` | `make schemas X4_GAME_DIR=...` | Extract XSD schemas from game |
| `schema-validate` | `make schema-validate` | Full XSD validation (slow) |
| `test` | `make test` | Run all tests |
| `clean` | `make clean` | Remove `dist/` |

### pyproject.toml

Manages x4cat as a development dependency:

```bash
cd my_balance_mod
uv sync        # install dependencies
```

After `uv sync`, all `x4cat` commands are available through `uv run`:

```bash
uv run x4cat list "$X4"
```

## Step 3: Add mod content

Add your mod files under `src/`. For example, to add a stat modification:

```bash
# Extract a ship macro
uv run x4cat extract-macro ship_arg_s_fighter_01_a_macro -o ./base/

# Copy for editing
cp -r ./base/ ./modified/

# Edit the macro
$EDITOR ./modified/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml

# Generate diff patch into src/
uv run x4cat xmldiff \
    --base ./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
    --mod  ./modified/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
    -o src/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml

# Clean up working directories
rm -rf base/ modified/
```

Or scaffold new content:

```bash
uv run x4cat scaffold ware --id quantum_tubes --name "Quantum Tubes" \
    --group hightech --price-avg 5000 -o ./src
```

## Step 4: Build

```bash
make build
```

This runs `x4cat pack src/ -o dist/ext_01.cat` and copies `content.xml` into `dist/`.

Output:

```
12 file(s) packed into dist/ext_01.cat
Build complete: dist/
```

## Step 5: Validate

### Structural validation

```bash
make validate
```

Runs `pytest` tests that check XML well-formedness and basic structural rules.

### Diff patch validation

```bash
make lint X4_GAME_DIR="$X4"
```

Runs `x4cat validate-diff` against the actual game files. This catches XPath selectors that do not match, which would cause silent failures in-game.

### Full pipeline

```bash
make all
```

Runs `validate`, `build`, and `test` in sequence. Use this before every commit.

## Step 6: Install

Copy the built mod to your extensions directory:

```bash
cp -r dist/ "$X4/extensions/my_balance_mod/"
```

Or create a symlink for development (so changes rebuild in place):

```bash
ln -s "$(pwd)/dist" "$X4/extensions/my_balance_mod"
```

## Step 7: Development workflow

The recommended development cycle:

```
edit src/ files
    |
    v
make lint X4_GAME_DIR="$X4"    -- catch broken XPaths early
    |
    v
make all                        -- validate + build + test
    |
    v
launch X4 with -prefersinglefiles    -- or test with packed catalog
    |
    v
check debug.log for errors
    |
    v
commit with conventional commit message
```

{: .note }
Use the `-prefersinglefiles` launch option during development to skip catalog packing. X4 will load loose files from `src/` directly if you place them in the extensions directory.

## Project conventions

### File naming

- MD scripts in `src/md/` **must be lowercase** or X4 silently ignores them
- Ware IDs should be lowercase with underscores
- Translation files follow the pattern `NNNN-lLLL.xml` (e.g., `0001-l044.xml` for English)

### Version numbering

The `version` attribute in `content.xml` is an integer: `100` means version 1.00, `210` means version 2.10.

### Git workflow

The template includes a `.gitignore` that excludes `dist/`, `schemas/`, and other generated files. Commit only source files.

## Next steps

- Follow the [stat mod tutorial](stat-mod) or [new ware tutorial](new-ware) to add content
- Read the [CLI Reference](../cli-reference) for all available commands
- See [extension_poc](https://github.com/meethune/extension_poc) for a working example project
