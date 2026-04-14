---
title: "UI / Lua Scripting"
layout: default
parent: "X4 Modding Reference"
nav_order: 8
---

# UI / Lua Scripting

X4's UI system is built with Lua scripts and XML layout definitions.

## Location

- `ui/addons/<addon_name>/` -- each UI addon is a self-contained directory
- Lua scripts (`.lua`) handle logic
- XML files define menu structures

## Base game UI addons

| Addon | Purpose |
|-------|---------|
| `ego_detailmonitor` | Main game menus (map, encyclopedia, ship config, station config, etc.) |
| `ego_interactmenu` | Right-click context menus |
| `ego_gameoptions` | Game settings menus |
| `ego_chatwindow` | Chat/communication window |
| `ego_debuglog` | Debug log viewer |
| `ego_targetmonitor` | Target info display |

## Notable Lua files

| File | Size | Purpose |
|------|------|---------|
| `menu_map.lua` | 1.5 MB | The map interface -- largest single script |
| `menu_ship_configuration.lua` | 521 KB | Ship loadout/configuration |
| `menu_station_configuration.lua` | 303 KB | Station building |
| `menu_playerinfo.lua` | 335 KB | Player info/empire overview |
| `menu_encyclopedia.lua` | 192 KB | In-game encyclopedia |
| `menu_diplomacy.lua` | 196 KB | Diplomatic relations |

## Modding UI

UI modding is significantly more constrained than XML modding:

- Lua files must use the **`.xpl` extension** (not `.lua`)
- UI XML files (`ui.xml`) **cannot be diff-patched** -- they must be fully replaced
- Replaced UI files must be packed in **`subst_NN.cat`** catalogs (which replace base game files), making them fragile across game updates
- Only **one mod** can replace a given Lua function -- multiple mods touching the same UI element will conflict

## kuertee's UI Extensions API

The community solution for multi-mod UI compatibility is [kuertee's UI Extensions](https://www.nexusmods.com/x4foundations/mods/552) ([GitHub](https://github.com/kuertee/x4-mod-ui-extensions)). It provides a callback-based system:

1. Get a pointer to the base game menu
2. Register a callback function
3. Write changes in the callback
4. Return what the callback expects

This allows multiple mods to modify the same UI element without conflict.

## Protected UI Mode

Introduced in X4 7.0/7.5, Protected UI Mode (`uisafemode` in config) is a security sandbox for the Lua UI layer. It prevents mods from executing arbitrary Lua code. Found in-game under **Settings > Extensions**.

**When enabled (default), it blocks:**
- Loading custom Lua files via mods
- Lua `require()` calls to non-whitelisted modules (only `ffi` is whitelisted)
- Named pipe connections for external program communication
- The legacy `Lua_Loader` MD signal method (`<raise_lua_event name="'Lua_Loader.Load'" .../>`)

**What it does NOT affect:**
- Pure XML-based MD scripts -- completely unaffected
- AI scripts (XML) -- completely unaffected
- Game data XML modifications (wares, ships, etc.) -- completely unaffected

**For mod developers:**
- The new recommended approach is to declare Lua files in `ui.xml` (loaded alongside base-game Lua), rather than the legacy MD signal method
- [SirNukes Mod Support APIs](https://github.com/bvbohnen/x4-projects/blob/master/extensions/sn_mod_support_apis/Readme.md) patches `require()` to allow mod Lua registration in protected mode via `Register_Require_Response`
- Disabling Protected UI Mode also disables some X4 online features (Ventures, Timelines leaderboards)

**For end users installing Lua mods:** disable Protected UI Mode via Settings > Extensions, then restart.

**References:**
- [Egosoft Forum: Protected UI mode discussion](https://forum.egosoft.com/viewtopic.php?t=469392)
- [SirNukes Mod Support APIs](https://github.com/bvbohnen/x4-projects/blob/master/extensions/sn_mod_support_apis/Readme.md)
- [kuertee UI Extensions](https://github.com/kuertee/x4-mod-ui-extensions/blob/master/README.md)

---
