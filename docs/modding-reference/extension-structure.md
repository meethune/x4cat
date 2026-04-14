---
title: "Extension Structure"
layout: default
parent: "X4 Modding Reference"
nav_order: 1
---

# Extension Structure

Every X4 mod is an **extension** -- a directory placed in `<X4 install>/extensions/<mod_id>/`.

## Minimum viable extension

```
extensions/my_mod/
  content.xml          -- Required. Extension manifest (always a loose file, never packed).
```

## Typical mod directory

```
extensions/my_mod/
  content.xml          -- Manifest
  ext_01.cat           -- Packed catalog index
  ext_01.dat           -- Packed catalog data
  md/                  -- Or packed inside ext_01.cat/dat
  aiscripts/
  libraries/
  t/
  ...
```

Mod files can be either **loose files** on disk or **packed into .cat/.dat catalogs**. Catalogs are preferred for distribution as they are faster to load and match the game's native format.

## content.xml

The extension manifest. X4 reads this as a loose file to determine whether and how to load the extension.

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="my_mod"
         version="100"
         name="My Mod Name"
         description="What this mod does"
         author="Your Name"
         date="2026-04-14"
         enabled="1"
         save="0">
  <!-- Minimum base game version required -->
  <dependency version="900" />

  <!-- Optional: depend on another extension (controls load order) -->
  <dependency id="ego_dlc_boron" version="100" optional="true" />
</content>
```

**Key attributes:**

| Attribute | Description |
|-----------|-------------|
| `id` | Unique identifier. Must match the directory name. Convention: lowercase, underscores. |
| `version` | Integer version number. Used for dependency checks. |
| `name` | Human-readable name shown in the Extension Manager. |
| `description` | Shown in the Extension Manager. |
| `enabled` | `"1"` to enable by default, `"0"` to disable. Users can toggle in-game. |
| `save` | `"1"` if the mod affects save games (most gameplay mods), `"0"` for cosmetic/UI-only. |
| `sync` | `"true"` if the mod must be synced in multiplayer Ventures. Usually `"false"`. |
| `date` | Publication date (informational). |

**Dependency element:**

| Attribute | Description |
|-----------|-------------|
| `version` | When no `id`: minimum base game version. When with `id`: minimum extension version. |
| `id` | Extension ID to depend on. Omit for base game dependency. |
| `optional` | `"true"` -- no error if missing. Controls load order only. |

## Load order

1. Base game catalogs (`01.cat` through `09.cat`) in numeric order
2. Extensions in dependency order, then alphabetical
3. Within each extension: `ext_01.cat` through `ext_NN.cat` in numeric order
4. Later files override earlier ones for the same virtual path

## Substitution catalogs

Extensions can use `subst_NN.cat` to override **base game** files directly (rather than adding extension-local files). In practice, DLCs do not use these -- `ext_NN.cat` with diff patching is the standard approach.

## Important rules

- MD script filenames in `md/` **must be lowercase** or X4 will silently ignore them.
- The extension directory name **must match** the `id` attribute in `content.xml`.
- Translation file page IDs must be globally unique across all loaded mods.
- Use `-prefersinglefiles` as a launch option during development to skip catalog packing and use loose files directly.
- If your mod diff-patches a DLC file, declare that DLC as a dependency in `content.xml`.

---
