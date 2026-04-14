---
title: Installation
layout: default
nav_order: 2
---

# Installation

## Requirements

- **Python 3.13** or newer
- **uv** -- fast Python package and project manager

x4cat is a pure-Python package with no compiled dependencies. It runs on Linux, macOS, and Windows (WSL).

## Install uv

If you do not already have uv installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See the [uv documentation](https://docs.astral.sh/uv/) for other install methods.

## Install x4cat

### Direct install (recommended)

Install x4cat as a standalone tool using uv:

```bash
uv tool install git+https://github.com/meethune/x4cat.git
```

This makes the `x4cat` command available globally without affecting your system Python.

### Clone and install from source

If you want to modify x4cat or run its test suite:

```bash
git clone https://github.com/meethune/x4cat.git
cd x4cat
uv sync
```

Run commands through uv when working from a clone:

```bash
uv run x4cat --help
```

## Verify installation

After installing, confirm x4cat is available:

```bash
x4cat --help
```

You should see output listing all available subcommands. Try listing files in your X4 game directory:

```bash
x4cat list "/path/to/X4 Foundations"
```

{: .note }
Replace `/path/to/X4 Foundations` with the actual path to your X4 installation. On Steam/Linux this is typically `~/.steam/steam/steamapps/common/X4 Foundations`.

## Upgrading

To upgrade to the latest version:

```bash
uv tool upgrade x4cat
```

Or if you installed from a clone:

```bash
cd x4cat
git pull
uv sync
```

## Uninstalling

```bash
uv tool uninstall x4cat
```
