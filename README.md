# x4cat

A Linux/cross-platform CLI and Python library for X4: Foundations `.cat/.dat` archives and mod development tooling.

Egosoft's [X Catalog Tool](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/X%20Catalog%20Tool/) is Windows-only — x4cat is a pure-Python reimplementation with additional modding tooling. Tested against X4 v9.00 game files.

**[Full documentation](https://meethune.github.io/x4cat/)**

## Features

**Archive operations:** list, extract, pack, diff `.cat/.dat` catalogs

**XML diff patching:** generate, validate, and check conflicts in `<diff>` patches

**Game data index:** build a SQLite index for instant asset inspection, search, and schema validation

**Content scaffolding:** generate boilerplate for new wares, equipment, ships, and translations

**Project scaffolding:** initialize complete mod projects with build pipeline, tests, and CI

## Install

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv tool install git+https://github.com/meethune/x4cat.git
```

## Quick start

```bash
# Build a game data index (one-time)
x4cat index "/path/to/X4 Foundations"

# Inspect any asset by ID
x4cat inspect ship_arg_s_fighter_01_a_macro
x4cat inspect energycells

# Search across wares, macros, components, datatypes, and keywords
x4cat search "fighter"
x4cat search "Energy Cells"          # search by in-game name
x4cat search "laser" --type macro

# List and extract game files
x4cat list "/path/to/X4 Foundations" -g 'md/*.xml'
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'libraries/wares.xml'

# Generate a diff patch from two XML files
x4cat xmldiff --base original.xml --mod modified.xml -o patch.xml

# Validate diff patches against the game
x4cat validate-diff "/path/to/X4 Foundations" ./src

# Scaffold new mod content
x4cat scaffold ware --id mymod_fuel --name "Super Fuel" --price-avg 500 -o src/
x4cat scaffold equipment --id mymod_engine_macro --name "Fast Engine" \
  --clone-from engine_arg_s_allround_01_mk1_macro -o src/

# Initialize a mod project
x4cat init my_mod --author "Name" --git

# Check for conflicts with other mods
x4cat check-conflicts ./my_mod/src ./other_mod/src
```

### Multi-version support

Use `--db` to work with multiple game versions:

```bash
x4cat index "/path/to/X4 v9.00" -o ~/.cache/x4cat/v900.db
x4cat index "/path/to/X4 v9.50-beta" -o ~/.cache/x4cat/v950.db

x4cat --db=~/.cache/x4cat/v900.db inspect energycells
x4cat --db=~/.cache/x4cat/v950.db search "new_ware"
```

## Mod development workflow

```bash
# 1. Extract base file, copy, edit
x4cat extract-macro ship_arg_s_fighter_01_a_macro -o ./base
cp -r ./base ./modified
# ... edit the macro ...

# 2. Generate diff patch
x4cat xmldiff --base ./base/assets/.../ship_macro.xml \
              --mod  ./modified/assets/.../ship_macro.xml \
              -o src/assets/.../ship_macro.xml

# 3. Validate everything
x4cat validate-diff "/path/to/X4 Foundations" src/
x4cat validate-translations src/
x4cat validate-schema src/

# 4. Build
x4cat pack src/ -o dist/ext_01.cat
```

See [extension_poc](https://github.com/meethune/extension_poc) for a complete mod project template with Makefile, tests, and CI.

## Documentation

- [Full documentation](https://meethune.github.io/x4cat/) — CLI reference, Python API, tutorials, X4 modding reference
- [extension_poc](https://github.com/meethune/extension_poc) — mod project template

## Running tests

```bash
uv run pytest
```

## License

MIT
