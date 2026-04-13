# x4cat

A Linux/cross-platform CLI for working with X4: Foundations `.cat/.dat` archives. Egosoft's [X Catalog Tool](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/X%20Catalog%20Tool/) is Windows-only, so this is a pure-Python reimplementation of the same functionality.

Tested against X4 v9.00 game files.

## What it does

- **List** files inside `.cat/.dat` archives
- **Extract** files to disk (preserves directory structure and timestamps)
- **Pack** loose files into new `.cat/.dat` catalogs (with append support)
- **Diff** two file trees and pack only the changed/new files into a catalog

It handles the override semantics correctly (later-numbered catalogs override earlier ones for the same path), and supports base game catalogs (`01.cat`), extension catalogs (`ext_01.cat`), and substitution catalogs (`subst_01.cat`).

## Install

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/meethune/x4cat.git
cd x4cat
uv sync
```

Or install directly:

```bash
uv tool install git+https://github.com/meethune/x4cat.git
```

## Usage

```bash
# list everything in your game install
x4cat list "/path/to/X4 Foundations"

# list just MD scripts
x4cat list "/path/to/X4 Foundations" -g 'md/*.xml'

# list with regex filtering
x4cat list "/path/to/X4 Foundations" --include '^aiscripts/' --exclude '\.xsd$'

# extract AI scripts
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'aiscripts/*'

# extract from a DLC extension
x4cat extract "/path/to/X4 Foundations/extensions/ego_dlc_boron" -o ./boron -p ext_

# pack loose files into a catalog
x4cat pack ./my_mod_files -o ./my_mod/ext_01.cat

# append to an existing catalog
x4cat pack ./extra_files -o ./my_mod/ext_01.cat --append

# diff two directories, pack only changes into a catalog
x4cat diff --base ./original --mod ./modified -o ./my_mod/ext_01.cat
```

Short aliases: `ls` for `list`, `x` for `extract`.

## Mod packaging workflow

The typical workflow for creating an X4 mod:

```bash
# 1. extract the files you want to modify
x4cat extract "/path/to/X4 Foundations" -o ./base -g 'libraries/wares.xml'

# 2. copy and edit
cp -r ./base ./modified
# ... edit files in ./modified ...

# 3. generate a diff catalog with only your changes
x4cat diff --base ./base --mod ./modified -o ./my_mod/ext_01.cat

# 4. add a content.xml to ./my_mod and drop it in X4's extensions/ folder
```

## Python API

```python
from pathlib import Path
from x4_catalog import build_vfs, extract_to_disk, list_entries, pack_catalog, diff_file_sets

game = Path("/path/to/X4 Foundations")

# build a virtual filesystem (dict of path -> CatEntry)
vfs = build_vfs(game)

# list with filtering
entries = list_entries(game, glob_pattern="md/*.xml")
entries = list_entries(game, include_re=r"^aiscripts/", exclude_re=r"\.xsd$")

# extract
extract_to_disk(game, Path("./unpacked"), glob_pattern="libraries/*")

# pack
pack_catalog(Path("./my_files"), Path("./ext_01.cat"))

# diff
changed, deleted = diff_file_sets(Path("./base"), Path("./modified"))
```

## Running tests

```bash
uv run pytest
```

## License

MIT
