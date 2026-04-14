---
title: "Maps, Components, and Macros"
layout: default
parent: "X4 Modding Reference"
nav_order: 9
---

# Maps, Components, and Macros

## Index files

Two master index files define the game's object registry:

- `index/components.xml` (318 KB) -- maps component names to XML definition files
- `index/macros.xml` (358 KB) -- maps macro names to XML definition files

These are how X4 resolves references like `macro.ship_arg_m_frigate_01_a_macro` -- it looks up the macro name in `index/macros.xml` to find the definition file.

## Components vs. Macros

- **Components** -- define the structural template of an object (mesh, collision, connections)
- **Macros** -- define a specific instance/variant of a component with concrete values (stats, loadouts)

Example: one frigate component can have multiple macros (Argon variant, Paranid variant, etc.)

## Map structure

Maps define the galaxy layout:

```
maps/
  xu_ep2_universe_macro.xml     -- main galaxy definition
  *_galaxy_macro.xml            -- individual galaxy definitions
```

## Index file registration

**Every new macro and component must be registered in the index files** or the game will not know they exist. This is the most common reason new content fails to appear.

For a new ship macro:

```xml
<!-- index/macros.xml diff patch -->
<diff>
  <add sel="/index">
    <entry name="my_ship_macro" value="extensions\my_mod\assets\units\size_m\macros\my_ship_macro" />
  </add>
</diff>
```

## Asset macro paths

When adding new content, macros go in standardized paths:

| Content type | Macro path |
|-------------|------------|
| Small ships (S) | `assets/units/size_s/macros/` |
| Medium ships (M) | `assets/units/size_m/macros/` |
| Large ships (L) | `assets/units/size_l/macros/` |
| Extra-large ships (XL) | `assets/units/size_xl/macros/` |
| Shields | `assets/props/SurfaceElements/macros/` |
| Weapons | `assets/props/WeaponSystems/<type>/macros/` |
| Turrets | `assets/props/WeaponSystems/integratedturrets/macros/` |

## Assets

The `assets/` directory tree contains 3D models, textures, animations, and other binary content:

```
assets/
  characters/     -- character models and animations
  environments/   -- environment/station meshes
  fx/             -- visual effects
  props/          -- prop objects (shields, weapons, turrets)
  ships/          -- ship models
  units/          -- unit macros by size class
  ...
```

Asset files use Egosoft's proprietary formats (`.xmf`, `.xpm`, `.xac`, `.xsm`).

---
