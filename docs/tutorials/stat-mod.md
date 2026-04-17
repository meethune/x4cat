---
title: Modify Ship/Weapon Stats
layout: default
parent: Tutorials
---

# Modify Existing Ship or Weapon Stats

This is the most common type of X4 mod -- changing the stats of an existing ship, weapon, engine, shield, or other equipment. You will use x4cat to extract the original game data, make your changes, and generate a diff patch that works alongside other mods.

## What you will build

A mod that modifies the Argon Nova (S-class fighter) to have more hull points and faster speed.

## Workflow overview

1. **Inspect** the asset to find its macro file
2. **Extract** the macro to a working directory
3. **Edit** the XML to change stats
4. **Generate a diff patch** using `xmldiff`
5. **Validate** the patch against the game
6. **Pack** into a catalog for distribution

## Step 1: Inspect the asset

First, find the macro you want to modify. If you know the macro name, skip ahead. Otherwise, search for it.

```bash
# Search for Argon fighters
x4cat search fighter --type macro
```

This returns a list of matching macros. Find the one you want:

```
  macro       ship_arg_s_fighter_01_a_macro  (assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml)
```

Now inspect it to see its current properties:

```bash
x4cat inspect ship_arg_s_fighter_01_a_macro
```

Output:

```
ship_arg_s_fighter_01_a_macro (ship_s)
  Macro: assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
  Component: assets/units/size_s/ship_arg_s_fighter_01.xml
  Price: 67830 / 79800 / 91770  (min / avg / max)
  Owners: argon, antigone
  Properties:
    hull.max: 3200
    purpose.primary: fight
    ship.type: fighter
```

## Step 2: Extract the macro

Extract the macro file to a `base/` directory:

```bash
x4cat extract-macro ship_arg_s_fighter_01_a_macro -o ./base/
```

This writes:

```
./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
```

Now copy it to a `modified/` directory for editing:

```bash
cp -r ./base/ ./modified/
```

## Step 3: Edit the stats

Open the file in your editor:

```bash
$EDITOR ./modified/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
```

The macro XML looks something like this:

```xml
<?xml version="1.0" encoding="utf-8"?>
<macros>
  <macro name="ship_arg_s_fighter_01_a_macro" class="ship_s">
    <component ref="ship_arg_s_fighter_01" />
    <properties>
      <identification name="{20101,30101}" ... />
      <hull max="3200" ... />
      <purpose primary="fight" />
      <ship type="fighter" />
      ...
    </properties>
  </macro>
</macros>
```

Make your changes. For example, double the hull and adjust speed:

- Change `<hull max="3200"` to `<hull max="6400"`
- Find the `<physics>` section and increase `<forward max="..."` values

Save the file.

## Step 4: Generate the diff patch

Use `xmldiff` to compare the base and modified versions:

```bash
x4cat xmldiff \
    --base ./base/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
    --mod  ./modified/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml \
    -o ./src/assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml
```

The generated diff patch will look something like:

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <replace sel="/macros/macro[@name='ship_arg_s_fighter_01_a_macro']/properties/hull/@max">6400</replace>
</diff>
```

This is a minimal patch that only changes what you modified. It does not replace the entire file, so it is compatible with other mods that patch the same ship.

## Step 5: Validate the patch

Check that every XPath selector in the diff patch matches an element in the base game:

```bash
x4cat validate-diff "$X4" ./src
```

Expected output:

```
assets/units/size_s/macros/ship_arg_s_fighter_01_a_macro.xml:2: PASS  sel="/macros/macro[@name='ship_arg_s_fighter_01_a_macro']/properties/hull/@max"  (1 element(s) matched)

1 file(s), 1 operation(s): 1 passed, 0 failed, 0 warning(s), 0 skipped
```

If you see `FAIL`, the XPath does not match the game file. Double-check your selectors.

## Step 6: Pack and install

Pack the diff patch into a catalog:

```bash
x4cat pack ./src -o ./dist/ext_01.cat
```

Create a `content.xml` for your mod:

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="my_stat_mod"
         version="100"
         name="Nova Hull Buff"
         description="Doubles Argon Nova hull strength"
         author="Your Name"
         date="2026-04-13"
         enabled="1"
         save="0">
  <dependency version="900" />
</content>
```

Install by copying to your extensions directory:

```bash
mkdir -p "$X4/extensions/my_stat_mod"
cp ./dist/ext_01.cat ./dist/ext_01.dat "$X4/extensions/my_stat_mod/"
cp content.xml "$X4/extensions/my_stat_mod/"
```

## Tips

- **Always diff-patch, never replace.** Replacing the full macro file breaks compatibility with other mods and game updates.
- **Use `validate-diff --strict`** before distributing your mod to catch any edge cases.
- **Set `save="0"`** in `content.xml` for stat-only mods that do not affect save games.
- For weapon mods, search with `x4cat search weapon --type macro` and follow the same workflow.
- Clean up your working directories when done: `rm -rf base/ modified/`

## Next steps

- [Set up a mod project](mod-project) with a Makefile for automated builds
- [Add new equipment](new-equipment) if you want to create entirely new items instead of modifying existing ones
