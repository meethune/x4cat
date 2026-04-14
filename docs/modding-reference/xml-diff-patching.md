---
title: "XML Diff Patching"
layout: default
parent: "X4 Modding Reference"
nav_order: 3
---

# XML Diff Patching

The most important modding technique. Instead of replacing entire game XML files (which breaks compatibility with other mods and game updates), you write **diff patches** that surgically modify specific elements.

**Reference:** [XML Diff Patching Wiki](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/XML%20Diff%20Patching/)

## How it works

When X4 loads a file like `libraries/wares.xml`, it first loads the base game version, then applies any diff patches found in extensions. A diff patch is an XML file with the **same virtual path** as the file it modifies, but with `<diff>` as the root element instead of the original root.

## Diff patch operations

The diff system supports three operations, selected via XPath in the `sel` attribute:

### Add

```xml
<diff>
  <!-- Add a child element to a parent -->
  <add sel="/wares">
    <ware id="my_custom_ware" name="{90001,1}" transport="container" volume="10">
      <price min="100" average="200" max="300" />
    </ware>
  </add>

  <!-- Add before a specific element -->
  <add sel="/wares/ware[@id='energycells']" pos="before">
    <ware id="my_ware_before_energy" ... />
  </add>

  <!-- Add after a specific element -->
  <add sel="/wares/ware[@id='energycells']" pos="after">
    <ware id="my_ware_after_energy" ... />
  </add>

  <!-- Add as the first child (prepend) -->
  <add sel="/wares" pos="prepend">
    <ware id="my_first_ware" ... />
  </add>

  <!-- Add an attribute -->
  <add sel="/wares/ware[@id='energycells']" type="@newtag">myvalue</add>
</diff>
```

### Replace

```xml
<diff>
  <!-- Replace an attribute value -->
  <replace sel="/wares/ware[@id='energycells']/price/@max">9999</replace>

  <!-- Replace an entire element -->
  <replace sel="/wares/ware[@id='energycells']/price">
    <price min="1" average="5" max="10" />
  </replace>

  <!-- Replace text content -->
  <replace sel="/wares/ware[@id='energycells']/@name">{90001,100}</replace>
</diff>
```

### Remove

```xml
<diff>
  <!-- Remove an element -->
  <remove sel="/wares/ware[@id='energycells']" />

  <!-- Remove an attribute -->
  <remove sel="/wares/ware[@id='energycells']/@tags" />
</diff>
```

## Conditional patching

All operations support an `if` attribute for conditional application:

```xml
<diff>
  <!-- Only apply if the DLC is loaded -->
  <add sel="/wares" if="/wares/ware[@id='boron_ware']">
    <ware id="my_boron_addon" ... />
  </add>

  <!-- Only apply if an element does NOT exist -->
  <add sel="/wares" if="not(/wares/ware[@id='my_ware'])">
    <ware id="my_ware" ... />
  </add>
</diff>
```

## Silent patching

Add `silent="true"` to suppress errors when the XPath does not match (useful for optional patches):

```xml
<replace sel="/wares/ware[@id='might_not_exist']/@value" silent="true">42</replace>
```

## Multi-element selection (msel)

X4 extends the diff format with an `msel` attribute that allows matching multiple elements in a single operation:

```xml
<!-- Modify multiple wares at once -->
<replace sel="//ware" msel="/wares/ware[@id='energycells'] | /wares/ware[@id='water']" />
```

## XPath reference for diff patches

Common XPath patterns used in X4 diff patches:

```
/root/element                       -- select by tag name
/root/element[@attr='value']        -- select by attribute
/root/element[2]                    -- select by position (1-based)
/root/element[@id='x']/child        -- nested selection
/root/element[@id='x']/@attr        -- select an attribute
//element                           -- recursive search (resilient to nesting changes)
//element[@attr='value']            -- recursive search with filter
```

**Tip:** Prefer `//` (recursive) selectors over absolute paths. They are more resilient to structural changes across game versions.

## Important notes

- The diff file must have the **exact same virtual path** as the file it patches
- The root element must be `<diff>`, not the original root element
- Multiple mods can diff-patch the same file -- they are applied in load order
- If a `sel` XPath does not match and `silent` is not set, X4 logs an error
- **Diff patching only works with extension catalogs (`ext_NN.cat`), not substitution catalogs**

## Generating and validating diff patches with x4cat

```bash
# Generate a diff from two XML files
x4cat xmldiff --base original.xml --mod modified.xml -o diff_patch.xml

# Validate all diff patches against the game
x4cat validate-diff "/path/to/X4 Foundations" ./src
```

## XSD schema for diff

The game ships a formal schema at `libraries/diff.xsd` defining the valid operations, XPath syntax, and attributes. Extract it for reference:

```bash
x4cat extract "/path/to/X4 Foundations" -o ./schemas -g 'libraries/diff.xsd'
```

---
