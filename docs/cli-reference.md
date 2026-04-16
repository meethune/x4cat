---
title: "CLI Reference"
layout: default
nav_order: 3
has_children: true
---

# CLI Reference

All commands follow the pattern:

```
x4cat [--db DB] <command> [arguments] [options]
```

Use `x4cat <command> --help` for built-in help on any subcommand.

## Global options

| Option | Description |
|--------|-------------|
| `--db DB` | Path to a specific index database. Supports multiple game versions by maintaining separate index DBs. Auto-detected from `~/.cache/x4cat/` if not provided. |

```bash
x4cat --db=~/.cache/x4cat/v900.db inspect ship_arg_s_fighter_01_a_macro
x4cat --db=/path/to/v850.db search "fighter"
x4cat --db=game.db list -g 'md/*.xml'
```

## Sections

| Section | Commands |
|---------|----------|
| [Archive Operations](archive-operations) | list, extract, pack, diff |
| [XML Diff Patching](xml-diff-patching) | xmldiff, validate-diff, validate-schema, check-conflicts, validate-translations |
| [Game Data Index](game-data-index) | index, inspect, search, extract-macro |
| [Scaffolding](scaffolding) | scaffold ware/equipment/ship/translation, init |
