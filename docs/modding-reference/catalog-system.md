---
title: "Catalog System (.cat/.dat)"
layout: default
parent: "X4 Modding Reference"
nav_order: 2
---

# Catalog System (.cat/.dat)

X4 uses a simple archive format: a `.cat` text index paired with a `.dat` binary blob.

## .cat format

Each line in a `.cat` file describes one entry:

```
<filepath> <size> <unix_mtime> <md5hex>
```

- **filepath** -- virtual path (may contain spaces; last 3 fields are always fixed)
- **size** -- file size in bytes
- **unix_mtime** -- Unix timestamp (seconds since epoch)
- **md5hex** -- MD5 checksum of the file content (32 hex chars)

Example:

```
libraries/wares.xml 790216 1775564527 1df31b1302a8db514139e40d6f975f30
md/diplomacy.xml 510865 1775564527 a553805a63d9e37cf5524907a11ef9cd
assets/some folder/file.xmf 456 888888 00112233445566778899aabbccddeeff
```

## .dat format

The `.dat` file stores file contents consecutively in the same order as `.cat` lines. No headers, no separators -- just raw bytes back-to-back. The offset of each file is computed by summing the sizes of all preceding entries.

## Naming conventions

| Pattern | Scope | Example |
|---------|-------|---------|
| `NN.cat` | Base game | `01.cat`, `02.cat`, ..., `09.cat` |
| `ext_NN.cat` | Extension-local | `ext_01.cat`, `ext_02.cat` |
| `subst_NN.cat` | Base game override | `subst_01.cat` |
| `*_sig.cat` | Signature catalogs | `01_sig.cat` (Egosoft DRM, ignored by mods) |
| `ext_vNNN.cat` | Version-specific | `ext_v610.cat` (loaded only on game version >= 6.10) |

## Override semantics

When multiple catalogs contain the same virtual path, the **last one loaded wins**. This means:
- `02.cat` overrides `01.cat` for the same path
- `ext_02.cat` overrides `ext_01.cat`
- Extension catalogs override base game catalogs
- This is how mods replace game files without modifying originals

## Base game catalogs (v9.00)

| Catalog | Index | Data | Content |
|---------|-------|------|---------|
| 01 | 12 MB (90,977 entries) | 10 GB | Assets (models, textures, animations, audio) |
| 02 | 221 KB | 850 MB | Additional assets |
| 03 | 31 MB | 5.8 GB | More assets (textures, models) |
| 04 | 13 KB | 848 MB | Large asset files |
| 05 | 318 KB | 198 MB | Mixed content |
| 06 | 51 KB | 2.8 MB | Shaders, scripts |
| 07 | 45 KB | 25 MB | Music, effects |
| 08 | 72 KB | 51 MB | UI, scripts, libraries |
| 09 | 1.1 KB | 99 MB | Translation files |

## Working with catalogs using x4cat

```bash
# List files in game install
x4cat list "/path/to/X4 Foundations"

# List with filtering
x4cat list "/path/to/X4 Foundations" -g 'md/*.xml'
x4cat list "/path/to/X4 Foundations" --include '^libraries/' --exclude '\.xsd$'

# Extract files
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'libraries/wares.xml'

# Extract from a DLC extension
x4cat extract "/path/to/X4 Foundations/extensions/ego_dlc_boron" -o ./boron -p ext_

# Pack mod files into a catalog
x4cat pack ./src -o ./dist/ext_01.cat
```

---
