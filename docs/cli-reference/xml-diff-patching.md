---
title: "XML Diff Patching"
layout: default
parent: "CLI Reference"
nav_order: 2
---

# XML Diff Patching
## xmldiff

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

## validate-diff

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

## validate-schema

Validate MD and AI scripts against schema rules indexed from the game's XSD files. Checks element names are valid in context and required attributes are present — in milliseconds instead of the 72 seconds that XSD compilation takes.

```
x4cat validate-schema <mod_dir> [--db DB] [--game-dir DIR]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `mod_dir` | Mod directory containing `md/` and/or `aiscripts/` |

**Options:**

| Option | Description |
|--------|-------------|
| `--db DB` | Index DB path (default: auto-detect) |
| `--game-dir DIR` | Game directory (auto-builds index if needed) |

**Checks performed:**
- **Unknown actions** — element inside `<actions>` not found in schema groups
- **Unknown conditions** — element inside `<conditions>` not found in schema groups
- **Missing required attributes** — required attributes from the schema not present

**Example:**

```bash
x4cat validate-schema src/

# Output:
#   ERROR: md/my_script.xml: unknown action <nonexistent_action>
#   WARN:  md/my_script.xml: <set_value> missing attribute 'name'
#
#   1 error(s), 1 warning(s)
```

{: .note }
Requires the schema to be indexed. Run `x4cat index <game_dir>` first, or use `--game-dir` to auto-build. The schema extraction adds XSD rules to the SQLite index alongside the existing wares/macros/components data.

---

## check-conflicts

Detect conflicts between two or more mods' diff patches by comparing their XPath selectors.

```
x4cat check-conflicts <mod_dir1> <mod_dir2> [mod_dir3 ...] [--verbose]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `mod_dirs` | Two or more mod directories to compare |

**Options:**

| Option | Description |
|--------|-------------|
| `--verbose` | Show safe overlaps (add+add) in addition to conflicts |

**Severity levels:**

| Level | Pattern | Risk |
|-------|---------|------|
| **CONFLICT** | `replace` + `replace` on same `sel`, or `remove` on a parent of another mod's `replace`/`add` | Last mod wins, first mod's change is silently lost |
| **INFO** | Mixed operations on the same `sel` that may interact | Depends on specifics |
| **SAFE** | Multiple `add` operations to the same parent | No conflict — all children get added |

**Example:**

```bash
x4cat check-conflicts ./my_mod ./other_mod

# Output:
#   CONFLICT  libraries/wares.xml  sel="/wares/ware[@id='energy']/price/@max"  mods: my_mod, other_mod
#
#   1 shared file(s): 1 conflict(s), 0 safe, 0 info

# With verbose:
x4cat check-conflicts ./my_mod ./other_mod --verbose

# Also shows:
#   SAFE      libraries/wares.xml  sel="/wares"  mods: my_mod, other_mod
```

Exit code is 0 if no conflicts, 1 if any CONFLICT detected.

---
