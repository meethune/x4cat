---
title: "Debugging"
layout: default
parent: "X4 Modding Reference"
nav_order: 13
---

# Debugging

## Debug log

X4 writes a debug log to:
- **Windows:** `%USERPROFILE%\Documents\Egosoft\X4\<save_id>\debug.log`
- **Linux:** `~/.config/EgoSoft/X4/<save_id>/debug.log`

## Launch parameters

Add these to the X4 launch options (Steam: right-click > Properties > Launch Options):

```
-debug all -logfile debuglog.txt -scriptlogfiles
```

| Parameter | Effect |
|-----------|--------|
| `-debug all` | Enable all debug output categories |
| `-logfile debuglog.txt` | Write debug output to a named file |
| `-scriptlogfiles` | Generate per-script log files for MD/AI scripts |
| `-prefersinglefiles` | Load loose files instead of catalogs (skip packing during development) |

## debug_text in MD/AI scripts

```xml
<debug_text text="'My debug message'" filter="general" />
<debug_text text="'Value: %s'.[$myVar]" filter="general" chance="100" />
```

The `chance` attribute (0-100) controls how often the message is logged. Use `chance="$DebugChance"` with a configurable variable to easily toggle verbosity.

## Debug filters

Use the `filter` attribute to categorize debug output:
- `general` -- general purpose
- `error` -- errors
- `scripts` / `scripts_verbose` -- script execution
- `economy_verbose` -- economic simulation
- `combat` -- combat events
- `fileio` -- file loading (shows all missing signature warnings)
- `savegame` -- save/load operations

## In-game debug tools

- **Debug Log Viewer** -- accessible in-game (Controls > General > Open Debug Log)
- **Extension Manager** -- shows loaded extensions and their status

## Common errors

| Error | Cause |
|-------|-------|
| `Could not find signature file` | Expected for mods -- harmless, Egosoft-only DRM |
| `Diff patch: no match for sel` | XPath in diff patch does not match target -- check selector |
| `XML parse error` | Malformed XML in mod file |
| `Unknown cue reference` | MD script references a cue that does not exist |
| `Macro not found` | Referenced macro is not registered in `index/macros.xml` |

---
