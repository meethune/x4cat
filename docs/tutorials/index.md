---
title: Tutorials
layout: default
nav_order: 5
has_children: true
---

# Tutorials

Step-by-step guides for common X4 modding workflows using x4cat.

These tutorials assume you have [installed x4cat](../installation) and have access to an X4: Foundations game directory. Each tutorial builds a working mod from scratch.

## Choose your tutorial

| Tutorial | Difficulty | What you will build |
|----------|------------|---------------------|
| [Modify Ship/Weapon Stats](stat-mod) | Beginner | A diff patch that changes an existing ship or weapon's properties |
| [Add a New Trade Ware](new-ware) | Beginner | A new trade good with pricing, production chain entry, and localization |
| [Add New Equipment](new-equipment) | Intermediate | A new engine, weapon, or shield cloned from an existing one |
| [Set Up a Mod Project](mod-project) | Beginner | A complete mod project with build pipeline, linting, and tests |

## Prerequisites

All tutorials require:

- x4cat installed and working (`x4cat --help` succeeds)
- Path to your X4: Foundations installation directory
- A text editor (VS Code with the [X4CodeComplete](https://www.nexusmods.com/x4foundations/mods/1721) extension is recommended)

Some tutorials also require:

- A game data index (built automatically on first use: `x4cat index "/path/to/X4 Foundations"`)

## Conventions used in tutorials

Throughout these tutorials:

- `$X4` refers to your X4 installation path (e.g., `~/.steam/steam/steamapps/common/X4 Foundations`)
- Commands are written for a Linux shell (bash/zsh)
- File paths use forward slashes
