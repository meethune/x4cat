---
title: Add New Equipment
layout: default
parent: Tutorials
---

# Add New Equipment (Engine/Weapon/Shield)

Adding new equipment to X4 requires more boilerplate than a trade ware: you need a macro file, index registration, a ware entry, and translation text. The `scaffold equipment` command generates all of these by cloning an existing item.

## What you will build

A mod that adds a custom medium shield generator cloned from the standard Mk1 shield, with adjusted stats.

## Workflow overview

1. **Search** for an existing item to clone
2. **Inspect** it to understand its properties
3. **Scaffold** the new equipment
4. **Customize** stats in the generated macro
5. **Validate** the diff patches
6. **Pack** and install

## Step 1: Find an item to clone

Search for existing shield generators:

```bash
x4cat search shield_gen --type macro --game-dir "$X4"
```

Sample output:

```
  macro       shield_gen_m_standard_01_mk1_macro  (assets/props/SurfaceElements/macros/shield_gen_m_standard_01_mk1_macro.xml)
  macro       shield_gen_m_standard_01_mk2_macro  (assets/props/SurfaceElements/macros/shield_gen_m_standard_01_mk2_macro.xml)
  macro       shield_gen_m_standard_01_mk3_macro  (assets/props/SurfaceElements/macros/shield_gen_m_standard_01_mk3_macro.xml)
```

## Step 2: Inspect the source

```bash
x4cat inspect shield_gen_m_standard_01_mk1_macro
```

```
shield_gen_m_standard_01_mk1_macro (shieldgenerator)
  Macro: assets/props/SurfaceElements/macros/shield_gen_m_standard_01_mk1_macro.xml
  Component: assets/props/SurfaceElements/shield_gen_m_standard_01.xml
  Price: 10030 / 11800 / 13570  (min / avg / max)
  Owners: argon, antigone, paranid, holyorder, teladi, ...
  Properties:
    recharge.max: 395
    recharge.rate: 101
    ...
```

This gives you the baseline stats to work with.

## Step 3: Scaffold the new equipment

```bash
x4cat scaffold equipment \
    --id shield_gen_m_heavy_01_macro \
    --name "Heavy Shield Mk1" \
    --clone-from shield_gen_m_standard_01_mk1_macro \
    --description "A reinforced shield generator with higher capacity but slower recharge" \
    --price-avg 20000 \
    --game-dir "$X4" \
    -o ./src
```

Generated files:

```
src/assets/props/SurfaceElements/macros/shield_gen_m_heavy_01_macro.xml   -- macro
src/index/macros.xml                                                       -- index registration
src/libraries/wares.xml                                                    -- ware entry
src/t/0001-l044.xml                                                        -- translation
```

## Step 4: Customize the macro

Open the generated macro file:

```bash
$EDITOR src/assets/props/SurfaceElements/macros/shield_gen_m_heavy_01_macro.xml
```

The file contains a cloned copy of the source macro with the new name and identification references. Modify the properties to differentiate your equipment:

```xml
<?xml version="1.0" encoding="utf-8"?>
<macros>
  <macro name="shield_gen_m_heavy_01_macro" class="shieldgenerator">
    <component ref="shield_gen_m_standard_01" />
    <properties>
      <identification name="{90001,1}" description="{90001,2}" />
      <recharge max="800" rate="50" delay="5" />
      <!-- other properties... -->
    </properties>
  </macro>
</macros>
```

In this example, we doubled the shield capacity (`max="800"`) but halved the recharge rate (`rate="50"`), creating a trade-off.

{: .note }
The `<component ref>` points to the original shield's 3D model. This means your new shield reuses the existing visual -- no 3D modeling required.

## Step 5: Review the other generated files

### Index registration (`src/index/macros.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <add sel="/index">
    <entry name="shield_gen_m_heavy_01_macro"
           value="assets\props\SurfaceElements\macros\shield_gen_m_heavy_01_macro" />
  </add>
</diff>
```

This diff patch registers your new macro in the game's macro index so X4 knows it exists.

### Ware entry (`src/libraries/wares.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <add sel="/wares">
    <ware id="shield_gen_m_heavy_01" name="{90001,1}" description="{90001,2}"
          transport="equipment" volume="1" tags="equipment shield">
      <price min="17000" average="20000" max="23000" />
      <component ref="shield_gen_m_heavy_01_macro" />
      <icon active="ware_default" video="ware_noicon_macro" />
    </ware>
  </add>
</diff>
```

### Translation (`src/t/0001-l044.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<language id="44">
  <page id="90001" title="shield_gen_m_heavy_01">
    <t id="1">Heavy Shield Mk1</t>
    <t id="2">A reinforced shield generator with higher capacity but slower recharge</t>
  </page>
</language>
```

## Step 6: Add faction owners (optional)

If you want factions to sell the equipment at their equipment docks, add `<owner>` elements to the ware entry in `src/libraries/wares.xml`:

```xml
      <owner faction="argon" />
      <owner faction="paranid" />
      <owner faction="teladi" />
```

Place these inside the `<ware>` element.

## Step 7: Validate

```bash
x4cat validate-diff "$X4" ./src
```

Check that all operations pass. The `index/macros.xml` patch targets `/index`, and `libraries/wares.xml` targets `/wares` -- both should match.

## Step 8: Pack and install

```bash
x4cat pack ./src -o ./dist/ext_01.cat
```

Create `content.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="heavy_shield_mod"
         version="100"
         name="Heavy Shield Mk1"
         description="Adds a heavy shield with high capacity and slow recharge"
         author="Your Name"
         date="2026-04-13"
         enabled="1"
         save="1">
  <dependency version="900" />
</content>
```

Install:

```bash
mkdir -p "$X4/extensions/heavy_shield_mod"
cp ./dist/ext_01.cat ./dist/ext_01.dat "$X4/extensions/heavy_shield_mod/"
cp content.xml "$X4/extensions/heavy_shield_mod/"
```

## Equipment types

The same workflow applies to all equipment types. The `scaffold equipment` command automatically detects the equipment class from the source macro:

| Source class | Generated tags | Example source macro |
|-------------|---------------|---------------------|
| `engine` | `engine equipment` | `engine_arg_m_allround_01_mk1_macro` |
| `shieldgenerator` | `equipment shield` | `shield_gen_m_standard_01_mk1_macro` |
| `weapon` | `equipment weapon` | `weapon_gen_m_laser_01_mk1_macro` |
| `turret` | `equipment turret` | `turret_arg_m_laser_01_mk1_macro` |
| `missile` | `equipment missile` | `missile_guided_light_mk1_macro` |

## Common issues

| Problem | Solution |
|---------|----------|
| Equipment does not appear at docks | Add `<owner faction="...">` elements to the ware |
| "Macro not found" error | Check `index/macros.xml` diff patch. The `name` must match your macro filename. |
| Stats are identical to source | You forgot to edit the macro file after scaffolding |

## Next steps

- [Set up a mod project](mod-project) to automate the build pipeline
- [Modify existing stats](stat-mod) if you only need to tweak an existing item
- See the [Scaffolding reference](../cli-reference/scaffolding) for ship scaffolding, which follows a similar pattern
