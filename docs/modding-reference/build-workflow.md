---
title: "Build Workflow with x4cat"
layout: default
parent: "X4 Modding Reference"
nav_order: 12
---

# Build Workflow with x4cat

## Recommended project structure

```
my_mod/
  content.xml          -- Extension manifest (loose file)
  src/                 -- Mod files (packed into catalog)
    md/                -- Mission Director scripts
    aiscripts/         -- AI scripts
    libraries/         -- Library diff patches
    t/                 -- Translation files
  dist/                -- Build output
  schemas/             -- Extracted XSD schemas (gitignored)
  tests/               -- Validation tests
  Makefile
  pyproject.toml       -- uv project with x4cat dev dependency
```

Use `x4cat init <mod_id>` to generate this structure automatically. See the [mod project tutorial](tutorials/mod-project) for a walkthrough.

## Build commands

```bash
# Pack mod files into a catalog
x4cat pack ./src -o ./dist/ext_01.cat
cp content.xml ./dist/

# Or use the diff workflow for iterative development
x4cat diff --base ./base --mod ./src -o ./dist/ext_01.cat
```

## Installation

Copy the contents of `dist/` to `<X4 install>/extensions/<mod_id>/`.

The directory must contain at minimum `content.xml`. If using catalogs, also `ext_01.cat` and `ext_01.dat`.

---
