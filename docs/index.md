---
title: Home
layout: home
nav_order: 1
---

# x4cat

A Linux/cross-platform CLI and Python library for working with X4: Foundations `.cat/.dat` archives.

Egosoft's [X Catalog Tool](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/X%20Catalog%20Tool/) is Windows-only. x4cat is a pure-Python reimplementation with additional modding tooling built for Linux and macOS.

## Quick install

```bash
uv tool install git+https://github.com/meethune/x4cat.git
```

Verify it works:

```bash
x4cat --help
```

## Features

### Archive operations

| Command | Description |
|---------|-------------|
| `list` (alias `ls`) | List files inside `.cat/.dat` archives with glob and regex filtering |
| `extract` (alias `x`) | Extract files to disk, preserving directory structure and timestamps |
| `pack` | Pack loose files into a `.cat/.dat` catalog pair |
| `diff` | Compare two directories and pack only changed/added files |

### XML diff patching

| Command | Description |
|---------|-------------|
| `xmldiff` | Generate an X4-compatible `<diff>` patch from two XML files |
| `validate-diff` | Validate diff patches against base game files, checking XPath selectors |
| `check-conflicts` | Detect conflicts between multiple mods' overlapping diff patches |
| `validate-schema` | Validate MD/AI scripts against indexed schema rules (fast, no XSD compilation) |

### Game data index

| Command | Description |
|---------|-------------|
| `index` | Build a SQLite index of game wares, macros, and components |
| `inspect` | Look up any asset by ware ID, macro name, or component name |
| `search` | Search assets by partial match across IDs, groups, and tags |
| `extract-macro` | Extract a macro file by ID, resolving its path through the index |

### Scaffolding

| Command | Description |
|---------|-------------|
| `scaffold ware` | Generate boilerplate for a new trade ware (diff patch + translation file) |
| `scaffold equipment` | Clone an existing engine/weapon/shield and generate all required files |
| `scaffold ship` | Clone an existing ship macro with index registration and ware entry |
| `scaffold translation` | Generate a translation stub for a new language from an existing file |
| `validate-translations` | Check that all text references have matching translation entries |
| `init` | Scaffold a complete mod project from a template with Makefile, tests, and CI |

## Documentation

- [Installation](installation) -- Python requirements, install methods, and verification
- [CLI Reference](cli-reference) -- Complete reference for all subcommands and arguments
- [Python API](python-api) -- Using x4cat as a library in your own scripts
- [Tutorials](tutorials/) -- Step-by-step guides for common modding workflows
- [X4 Modding Reference](modding-reference) -- Comprehensive reference for X4 extension development

## Related projects

- [extension_poc](https://github.com/meethune/extension_poc) -- Mod project template with build pipeline, linting, and tests
- [Egosoft Modding Wiki](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/) -- Official modding documentation
