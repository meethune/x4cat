# x4cat

A Linux/cross-platform CLI for working with X4: Foundations `.cat/.dat` archives. Egosoft's [X Catalog Tool](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/X%20Catalog%20Tool/) is Windows-only, so this is a pure-Python reimplementation of the same functionality.

Tested against X4 v9.00 game files.

## What it does

- **List** files inside `.cat/.dat` archives
- **Extract** files to disk (preserves directory structure and timestamps)
- **Pack** loose files into new `.cat/.dat` catalogs (with append support)
- **Diff** two file trees and pack only the changed/new files into a catalog
- **Xmldiff** two XML files and generate an X4-compatible `<diff>` patch
- **Validate** XML diff patches against base game files

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

### List and extract

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
```

Short aliases: `ls` for `list`, `x` for `extract`.

### Pack and diff

```bash
# pack loose files into a catalog
x4cat pack ./my_mod_files -o ./my_mod/ext_01.cat

# append to an existing catalog
x4cat pack ./extra_files -o ./my_mod/ext_01.cat --append

# diff two directories, pack only changes into a catalog
x4cat diff --base ./original --mod ./modified -o ./my_mod/ext_01.cat
```

### XML diff patches

Generate X4-compatible `<diff>` patches from two XML files instead of replacing files wholesale:

```bash
# generate a diff patch (stdout)
x4cat xmldiff --base ./original/libraries/wares.xml --mod ./modified/libraries/wares.xml

# generate a diff patch (file)
x4cat xmldiff --base ./original/libraries/wares.xml --mod ./modified/libraries/wares.xml \
  -o ./my_mod/src/libraries/wares.xml
```

The generated patch uses `@id`/`@name` attributes for stable XPath selectors.

### Validate diff patches

Check that every XPath selector in your diff patches matches the base game files:

```bash
x4cat validate-diff "/path/to/X4 Foundations" ./my_mod/src

# output:
# libraries/wares.xml:3: PASS  sel="/wares/ware[@id='energy']"  (1 element(s) matched)
# libraries/wares.xml:6: FAIL  sel="/wares/ware[@id='nonexistent']"  (no elements matched)
#
# 1 file(s), 2 operation(s): 1 passed, 1 failed, 0 warning(s), 0 skipped
```

Use `--strict` to treat unsupported XPath warnings as errors.

## Mod packaging workflow

The typical workflow for creating an X4 mod:

```bash
# 1. extract the files you want to modify
x4cat extract "/path/to/X4 Foundations" -o ./base -g 'libraries/wares.xml'

# 2. copy and edit
cp -r ./base ./modified
# ... edit files in ./modified ...

# 3. generate XML diff patches (recommended)
x4cat xmldiff --base ./base/libraries/wares.xml --mod ./modified/libraries/wares.xml \
  -o ./my_mod/src/libraries/wares.xml

# 4. validate your patches against the game
x4cat validate-diff "/path/to/X4 Foundations" ./my_mod/src

# 5. pack into a catalog
x4cat pack ./my_mod/src -o ./my_mod/dist/ext_01.cat

# 6. add a content.xml and drop it in X4's extensions/ folder
```

See [extension_poc](https://github.com/meethune/extension_poc) for a complete mod project template with build pipeline.

## Python API

```python
from pathlib import Path
from x4_catalog import (
    build_vfs, extract_to_disk, list_entries, pack_catalog,
    diff_file_sets, generate_diff, validate_diff_directory,
)

game = Path("/path/to/X4 Foundations")

# build a virtual filesystem (dict of path -> CatEntry)
vfs = build_vfs(game)

# list with filtering
entries = list_entries(game, glob_pattern="md/*.xml")

# extract
extract_to_disk(game, Path("./unpacked"), glob_pattern="libraries/*")

# pack
pack_catalog(Path("./my_files"), Path("./ext_01.cat"))

# generate XML diff patch
base_xml = Path("base/libraries/wares.xml").read_bytes()
mod_xml = Path("mod/libraries/wares.xml").read_bytes()
diff_patch = generate_diff(base_xml, mod_xml)

# validate diff patches against game files
reports = validate_diff_directory(game, Path("./my_mod/src"))
```

## Running tests

```bash
uv run pytest
```

## License

MIT
