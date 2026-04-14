---
title: "In-Game Reference Files"
layout: default
parent: "X4 Modding Reference"
nav_order: 11
---

# In-Game Reference Files

X4 ships interactive reference files that document all available script operations, properties, and keywords. Extract these for offline use:

```bash
x4cat extract "/path/to/X4 Foundations" -o ./reference -g '*.html'
x4cat extract "/path/to/X4 Foundations" -o ./reference -g 'libraries/scriptproperties.*'
```

## Available references

| File | Description |
|------|-------------|
| `scriptproperties.html` | Interactive HTML reference for all MD/AI script properties, keywords, and datatypes. Open in a browser. |
| `libraries/scriptproperties.xml` | Machine-readable script properties (329 KB) |
| `libraries/scriptproperties.xsd` | Schema for scriptproperties.xml |
| `libraries/scriptproperties.xsl` | XSLT stylesheet for rendering scriptproperties.xml |
| `jobeditor.html` | Job definition editor/reference |

The `scriptproperties.html` file is the single most useful modding reference -- it documents every expression, property, event, action, and datatype available in MD and AI scripts.

**VS Code integration:** The [X4CodeComplete](https://www.nexusmods.com/x4foundations/mods/1721) VS Code extension provides autocompletion and syntax highlighting for X4 XML using these schema files.

---
