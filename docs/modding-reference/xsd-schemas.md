---
title: "XSD Schemas"
layout: default
parent: "X4 Modding Reference"
nav_order: 10
---

# XSD Schemas

X4 ships 41 XSD schema files that formally define the structure of its XML files. These are invaluable for validation during mod development.

## Extracting schemas

```bash
x4cat extract "/path/to/X4 Foundations" -o ./schemas -g '*.xsd'
```

## Schema hierarchy

```
md/md.xsd                    -- includes ../libraries/md.xsd
aiscripts/aiscripts.xsd      -- includes ../libraries/aiscripts.xsd
libraries/md.xsd              -- includes common.xsd
libraries/aiscripts.xsd       -- includes common.xsd
libraries/common.xsd          -- base types and expressions (40K lines)
libraries/diff.xsd            -- diff patching operations
libraries/libraries.xsd       -- library file structures
```

## Key schemas

| Schema | Lines | Purpose |
|--------|-------|---------|
| `libraries/common.xsd` | 40,572 | Base types, expression language, variables |
| `libraries/md.xsd` | 4,919 | Mission Director elements and attributes |
| `libraries/aiscripts.xsd` | -- | AI script elements |
| `libraries/diff.xsd` | -- | Diff patch operations (add/replace/remove) |
| `libraries/parameters.xsd` | -- | Game parameter definitions |
| `libraries/libraries.xsd` | -- | Library XML structures |

## Validation

Full XSD validation is slow (~70 seconds) due to the size of `common.xsd`. For development, use structural checks (correct root element, required attributes) and reserve full XSD validation for pre-release verification.

```bash
# Fast: structural validation
xmllint --noout src/md/*.xml

# Slow but thorough: full XSD validation
xmllint --schema schemas/md/md.xsd --noout src/md/my_script.xml
```

Or use the extension_poc template's `make schema-validate` target.

---
