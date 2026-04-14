---
title: "Localization (Translation Files)"
layout: default
parent: "X4 Modding Reference"
nav_order: 7
---

# Localization (Translation Files)

## Location

Translation files live in `t/` with the naming pattern `NNNN-lLLL.xml`:
- `NNNN` -- page group number (e.g., `0001` for core game text)
- `LLL` -- language code

## Language codes

| Code | Language |
|------|----------|
| 7 | Russian |
| 33 | French |
| 34 | Spanish |
| 39 | Italian |
| 42 | Czech |
| 44 | English |
| 48 | Polish |
| 49 | German |
| 55 | Portuguese |
| 81 | Japanese |
| 82 | Korean |
| 86 | Simplified Chinese |
| 88 | Traditional Chinese |

## File format

```xml
<?xml version="1.0" encoding="utf-8"?>
<language id="44">
  <page id="90001" title="My Mod" descr="Custom mod strings" voice="no">
    <t id="1">My Custom Ware</t>
    <t id="2">A custom ware added by my mod</t>
    <t id="100">Mission briefing text here</t>
  </page>
</language>
```

## Usage in other XML

Reference text with `{pageId,entryId}`:

```xml
<ware id="my_ware" name="{90001,1}" description="{90001,2}" />
```

## In MD scripts

```xml
<set_value name="$text" exact="{90001,1}" />
<debug_text text="'Ware name: ' + {90001,1}" />
```

## Best practices

- Use page IDs **90000+** for custom mods to avoid conflicts with base game and other mods
- Always provide at least English (`l044`) translations
- Translation files can be diff-patched to add pages to existing files, or provided as new files

---
