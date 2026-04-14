---
title: "Libraries (Game Data XML)"
layout: default
parent: "X4 Modding Reference"
nav_order: 6
---

# Libraries (Game Data XML)

The `libraries/` directory contains the game's core data definitions -- the "database" of game objects, their properties, and relationships.

## Key library files

| File | Content | Common mod use |
|------|---------|----------------|
| `wares.xml` | All trade goods, their prices, production chains | Add custom wares, modify prices |
| `jobs.xml` | NPC ship/station spawn rules | Add/modify NPC spawns |
| `factions.xml` | Faction definitions, relations | Add factions, change relations |
| `god.xml` | Galaxy layout, cluster/sector definitions | Add sectors, modify maps |
| `modules.xml` | Station module definitions | Add station modules |
| `loadouts.xml` | Ship/station equipment loadouts | Modify default loadouts |
| `gamestarts.xml` | Game start scenarios | Add custom game starts |
| `constructionplans.xml` | Station blueprints | Add/modify construction plans |
| `defaults.xml` | Default game values and constants | Tweak game balance |
| `parameters.xml` | Detailed game parameters | Fine-tune mechanics |
| `effects.xml` | Visual/gameplay effects | Add custom effects |
| `characters.xml` | NPC character definitions | Add/modify NPCs |
| `baskets.xml` | Item/ship groupings | Modify trade/spawn pools |
| `mapdefaults.xml` | Default map resource/population values | Modify sector richness |
| `drops.xml` | Loot drop tables | Modify drop rates |
| `diplomacy.xml` | Diplomatic action definitions | Modify diplomacy options |

## Modding libraries with diff patches

Libraries should almost always be modified via diff patching (not full replacement) for compatibility:

```xml
<!-- libraries/wares.xml diff patch: add a new ware -->
<diff>
  <add sel="/wares">
    <ware id="my_custom_ware"
          name="{90001,1}"
          description="{90001,2}"
          group="hightech"
          transport="container"
          volume="20"
          tags="container economy">
      <price min="500" average="1000" max="1500" />
      <production time="600" amount="10" method="default" name="{20206,101}">
        <primary>
          <ware ware="energycells" amount="50" />
          <ware ware="refinedmetals" amount="30" />
        </primary>
        <effects>
          <effect type="work" product="0.5" />
        </effects>
      </production>
      <icon active="ware_default" video="ware_noicon_macro" />
    </ware>
  </add>
</diff>
```

## Ware text references

Text in wares uses the format `{pageId,entryId}`:
- `name="{20201,101}"` -- references page 20201, entry 101 in translation files
- Custom mods should use page IDs 90000+ to avoid conflicts

## Production chain example

From `wares.xml` -- Advanced Composites:

```xml
<ware id="advancedcomposites" name="{20201,401}" group="hightech"
      transport="container" volume="32" tags="container economy stationbuilding">
  <price min="432" average="540" max="648" />
  <production time="300" amount="54" method="default" name="{20206,101}">
    <primary>
      <ware ware="energycells" amount="50" />
      <ware ware="graphene" amount="80" />
      <ware ware="refinedmetals" amount="80" />
    </primary>
    <effects>
      <effect type="work" product="0.34" />
    </effects>
  </production>
</ware>
```

---
