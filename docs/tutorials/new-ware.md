---
title: Add a New Trade Ware
layout: default
parent: Tutorials
---

# Add a New Trade Ware

Trade wares are the simplest type of new content to add to X4. A ware only requires a diff patch to `libraries/wares.xml` and a translation file -- no 3D models, macros, or index registration.

## What you will build

A mod that adds "Quantum Tubes" -- a new high-tech trade good that stations can produce and ships can trade.

## Workflow overview

1. **Scaffold** the ware boilerplate
2. **Customize** the generated files
3. **Validate** the diff patch
4. **Pack** into a catalog
5. **Install** and test

## Step 1: Scaffold the ware

Use the `scaffold ware` command to generate the boilerplate:

```bash
x4cat scaffold ware \
    --id quantum_tubes \
    --name "Quantum Tubes" \
    --description "High-energy containment tubes used in advanced quantum devices" \
    --group hightech \
    --volume 10 \
    --price-avg 5000 \
    -o ./src
```

This creates two files:

```
src/libraries/wares.xml     -- diff patch adding the ware to the game
src/t/0001-l044.xml         -- English translation file
```

## Step 2: Review the generated files

### Wares diff patch

Open `src/libraries/wares.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <add sel="/wares">
    <ware id="quantum_tubes" name="{90001,1}" description="{90001,2}"
          group="hightech" transport="container" volume="10"
          tags="container economy">
      <price min="4250" average="5000" max="5750" />
      <icon active="ware_default" video="ware_noicon_macro" />
    </ware>
  </add>
</diff>
```

The scaffold auto-derived min/max prices as +/-15% of the average. Adjust these if needed.

### Translation file

Open `src/t/0001-l044.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<language id="44">
  <page id="90001" title="quantum_tubes">
    <t id="1">Quantum Tubes</t>
    <t id="2">High-energy containment tubes used in advanced quantum devices</t>
  </page>
</language>
```

Text references use page 90001 (entries 1 and 2), which are referenced from the ware definition as `{90001,1}` and `{90001,2}`.

## Step 3: Customize (optional)

### Add a production recipe

To make the ware producible at stations, add a `<production>` element inside the `<ware>`:

Edit `src/libraries/wares.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<diff>
  <add sel="/wares">
    <ware id="quantum_tubes" name="{90001,1}" description="{90001,2}"
          group="hightech" transport="container" volume="10"
          tags="container economy">
      <price min="4250" average="5000" max="5750" />
      <production time="600" amount="50" method="default" name="{20206,101}">
        <primary>
          <ware ware="energycells" amount="100" />
          <ware ware="refinedmetals" amount="40" />
        </primary>
        <effects>
          <effect type="work" product="0.34" />
        </effects>
      </production>
      <icon active="ware_default" video="ware_noicon_macro" />
    </ware>
  </add>
</diff>
```

This means: every 600 seconds, a station module produces 50 Quantum Tubes from 100 Energy Cells and 40 Refined Metals.

### Add faction owners

To make factions produce and sell the ware, add `<owner>` elements:

```xml
      <owner faction="argon" />
      <owner faction="paranid" />
      <owner faction="teladi" />
```

Place these inside the `<ware>` element, after `<icon>`.

## Step 4: Validate the diff patch

```bash
x4cat validate-diff "$X4" ./src
```

Expected output:

```
libraries/wares.xml:2: PASS  sel="/wares"  (root element matched)

1 file(s), 1 operation(s): 1 passed, 0 failed, 0 warning(s), 0 skipped
```

The selector `/wares` matches the root element of `libraries/wares.xml`, confirming the diff patch will apply correctly.

## Step 5: Pack and install

Pack the mod files:

```bash
x4cat pack ./src -o ./dist/ext_01.cat
```

Create `content.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="quantum_tubes_mod"
         version="100"
         name="Quantum Tubes"
         description="Adds Quantum Tubes trade ware"
         author="Your Name"
         date="2026-04-13"
         enabled="1"
         save="1">
  <dependency version="900" />
</content>
```

{: .note }
Set `save="1"` because adding a new ware affects the game economy and save data.

Install:

```bash
mkdir -p "$X4/extensions/quantum_tubes_mod"
cp ./dist/ext_01.cat ./dist/ext_01.dat "$X4/extensions/quantum_tubes_mod/"
cp content.xml "$X4/extensions/quantum_tubes_mod/"
```

## Step 6: Test in-game

1. Launch X4 and check the Extension Manager -- your mod should appear
2. Load or start a game
3. Open the Encyclopedia and search for "Quantum Tubes" to verify the ware exists
4. Check the trade menus at stations to see if the ware is being produced and traded

## Common issues

| Problem | Solution |
|---------|----------|
| Ware does not appear | Check that the diff patch `sel="/wares"` matches. Run `validate-diff`. |
| Name shows as `{90001,1}` | Translation file is missing or has wrong page/entry ID |
| No stations produce it | Add `<production>` and `<owner>` elements |
| Page ID conflict | Another mod uses page 90001. Change to a different page ID (90002, etc.) and update both files. |

## Next steps

- [Set up a mod project](mod-project) to automate building and testing
- [Add new equipment](new-equipment) to create items that need macros and index registration
- Read the [X4 Modding Reference](../modding-reference) for details on production chains, ware groups, and tags
