---
title: Home
layout: home
nav_order: 1
---

# x4cat

A Linux/cross-platform CLI for working with X4: Foundations `.cat/.dat` archives.

Egosoft's [X Catalog Tool](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/X%20Catalog%20Tool/) is Windows-only — x4cat is a pure-Python reimplementation with additional modding tooling.

{: .note }
Documentation is under construction. See the [README](https://github.com/meethune/x4cat) for current usage.

## Features

- **List, extract, pack** `.cat/.dat` archives
- **Generate XML diff patches** from file comparisons
- **Validate diff patches** against base game files
- **Index game data** into SQLite for fast lookups
- **Inspect and search** wares, macros, and components by ID
- **Scaffold** new mod content (wares, equipment, ships)
- **Initialize** new mod projects from a template

## Quick start

```bash
uv tool install git+https://github.com/meethune/x4cat.git
x4cat list "/path/to/X4 Foundations"
```
