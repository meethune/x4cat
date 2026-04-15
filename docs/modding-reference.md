---
title: "X4 Modding Reference"
layout: default
nav_order: 6
has_children: true
---

# X4: Foundations Modding Reference

A comprehensive reference for developing X4: Foundations mods (extensions). Compiled from Egosoft's official documentation, game file analysis (v9.00), and community resources.

## Sections

| Topic | Description |
|-------|-------------|
| [Extension Structure](extension-structure) | content.xml manifest, load order, substitution catalogs |
| [Catalog System](catalog-system) | .cat/.dat format, naming conventions, override semantics |
| [XML Diff Patching](xml-diff-patching) | add/replace/remove operations, XPath, conditional patching |
| [Mission Director](mission-director) | MD scripting: cues, events, actions, variables |
| [AI Scripts](ai-scripts) | Ship/NPC behavior: orders, interrupts, attention levels |
| [Libraries](libraries) | Game data XML: wares, jobs, factions, modules |
| [Localization](localization) | Translation files, language codes, text references |
| [UI / Lua Scripting](ui-lua-scripting) | Lua UI modding, Protected UI Mode, kuertee API |
| [Maps, Components, Macros](maps-components-macros) | Index files, macro paths, asset structure |
| [XSD Schemas](xsd-schemas) | Schema hierarchy, extraction, validation |
| [In-Game References](in-game-references) | scriptproperties.html, jobeditor, VS Code integration |
| [Build Workflow](build-workflow) | Project structure, build commands, installation |
| [Debugging](debugging) | Debug log, launch parameters, common errors |
| [Common Recipes](common-recipes) | Add wares, modify values, MD scripts, NPC jobs, ships |
| [File Types](file-types) | All file extensions in game archives |
| [Signature Files](signature-files) | RSA signatures, DRM, impact on mods |
| [Common Pitfalls](common-pitfalls) | Top 10 recurring modding mistakes |
| [Quick Reference Links](quick-reference-links) | All official, tool, and community URLs |

## External resources

**Official:**
- [Egosoft Modding Support Wiki](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/)
- [Egosoft Forum -- Tools, Tutorials & Resources Index](https://forum.egosoft.com/viewtopic.php?f=181&t=402382)

**Community:**
- [Nexus Mods X4](https://www.nexusmods.com/x4foundations)
- [Getting into X4 modding on Linux](https://beko.famkos.net/2021/05/01/getting-into-x4-foundations-modding-on-linux/)

**Example mods:**
- [Genesis Signal](https://github.com/Vectorial1024/v1024_genesis_signal) -- MD game-start event detection
- [DeadAir Scripts](https://github.com/DeadAirRT/deadair_scripts) -- AI script modifications
- [kuertee UI Extensions](https://github.com/kuertee/x4-mod-ui-extensions) -- Lua UI callback system
