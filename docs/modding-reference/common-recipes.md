---
title: "Common Modding Recipes"
layout: default
parent: "X4 Modding Reference"
nav_order: 14
---

# Common Modding Recipes

## Add a new ware

1. Create `src/libraries/wares.xml` as a diff patch:

```xml
<diff>
  <add sel="/wares">
    <ware id="my_ware" name="{90001,1}" description="{90001,2}"
          group="hightech" transport="container" volume="20"
          tags="container economy">
      <price min="500" average="1000" max="1500" />
      <production time="600" amount="10" method="default" name="{20206,101}">
        <primary>
          <ware ware="energycells" amount="50" />
        </primary>
      </production>
      <icon active="ware_default" video="ware_noicon_macro" />
    </ware>
  </add>
</diff>
```

2. Create `src/t/0001-l044.xml` for English text:

```xml
<?xml version="1.0" encoding="utf-8"?>
<language id="44">
  <page id="90001" title="My Mod">
    <t id="1">My Custom Ware</t>
    <t id="2">A special ware added by my mod</t>
  </page>
</language>
```

Or use `x4cat scaffold ware` to generate both files automatically. See the [new ware tutorial](tutorials/new-ware).

## Modify a game value

Diff patch `libraries/wares.xml` to change energy cell price:

```xml
<diff>
  <replace sel="/wares/ware[@id='energycells']/price/@max">100</replace>
</diff>
```

## Add an MD script that runs on game start

Create `src/md/my_mod.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<mdscript name="MyMod" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:noNamespaceSchemaLocation="md.xsd">
  <cues>
    <cue name="Start" instantiate="false" namespace="this">
      <conditions>
        <event_cue_signalled cue="md.Setup.Start" />
      </conditions>
      <actions>
        <debug_text text="'MyMod initialized'" filter="general" />
        <show_notification text="{90001,100}" />
      </actions>
      <cues>
        <cue name="PeriodicCheck" instantiate="true" checkinterval="60s">
          <conditions>
            <check_value value="player.money gt 1000000" />
          </conditions>
          <actions>
            <debug_text text="'Player is rich!'" filter="general" />
          </actions>
        </cue>
      </cues>
    </cue>
  </cues>
</mdscript>
```

## Add NPC jobs (ship spawns)

Diff patch `libraries/jobs.xml`:

```xml
<diff>
  <add sel="/jobs">
    <job id="my_patrol_job">
      <quotas galaxy="5" />
      <location class="sector" faction="argon" />
      <ship macro="macro.ship_arg_m_frigate_01_a_macro">
        <owner exact="faction.argon" />
      </ship>
    </job>
  </add>
</diff>
```

## Add a new ship to a faction's wharves

This requires touching multiple files:

1. `index/macros.xml` -- register the ship macro
2. `index/components.xml` -- register the ship component
3. `assets/units/size_m/macros/my_ship_macro.xml` -- ship properties (hull, speed, etc.)
4. `libraries/wares.xml` -- ware entry with `<owner>` elements for each selling faction
5. `t/0001-l044.xml` -- ship name and description
6. Optionally: `libraries/loadouts.xml` -- default equipment loadout

If a new ship does not appear at wharves, the most common causes are:
- Missing `index/macros.xml` entry
- Missing `<owner faction="...">` for the faction at that wharf
- Missing ware entry in `libraries/wares.xml`

Use `x4cat scaffold ship` to generate all of these files automatically.

---
