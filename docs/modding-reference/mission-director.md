---
title: "Mission Director (MD) Scripts"
layout: default
parent: "X4 Modding Reference"
nav_order: 4
---

# Mission Director (MD) Scripts

MD scripts drive game logic: missions, faction behavior, event responses, UI triggers, and more. They are XML-based state machines using a cue/condition/action pattern.

**Reference:** [Mission Director Guide](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/)

## Location

- Base game: `md/*.xml`
- Extensions: `md/*.xml` (in catalog or loose)
- Schema: `libraries/md.xsd` (includes `libraries/common.xsd` -- 45K lines total)

## Basic structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<mdscript name="MyModScript"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:noNamespaceSchemaLocation="md.xsd">
  <cues>
    <cue name="Start" instantiate="false" namespace="this">
      <conditions>
        <check_any>
          <event_game_started />
          <event_game_loaded />
        </check_any>
      </conditions>
      <actions>
        <debug_text text="'My mod loaded'" filter="general" />
      </actions>
      <cues>
        <!-- Nested cues go here -->
      </cues>
    </cue>
  </cues>
</mdscript>
```

## Key concepts

**Cues** are the basic unit of MD scripts. Each cue has:
- **Conditions** -- when to trigger (events + checks)
- **Actions** -- what to do when triggered
- **Nested cues** -- child cues that become active after the parent fires

**Cue attributes:**

| Attribute | Values | Description |
|-----------|--------|-------------|
| `name` | PascalCase string | Unique name within the script. Must start with uppercase. |
| `instantiate` | `true`/`false` | If `true`, creates a new instance each time conditions are met. If `false`, fires once. |
| `namespace` | `this`/`static` | `this` = instance-scoped variables, `static` = shared across instances. |
| `checkinterval` | time expression | How often to re-evaluate conditions (e.g., `5s`, `1min`). |
| `checktime` | time expression | Wait this long before first condition check. |

## Common events

```xml
<!-- Game lifecycle -->
<event_game_started />
<event_game_loaded />

<!-- Object events -->
<event_object_destroyed object="..." />
<event_object_signalled object="..." param="..." />
<event_object_changed_zone object="..." />

<!-- Player events -->
<event_player_changed_sector />
<event_player_changed_zone />

<!-- Faction events -->
<event_faction_relation_changed faction="..." otherfaction="..." />

<!-- Signal-based (mod inter-communication) -->
<event_cue_signalled cue="md.OtherScript.SomeCue" />
<event_cue_completed cue="md.OtherScript.SomeCue" />
```

## Common actions

```xml
<!-- Debug output (visible in debug log) -->
<debug_text text="'message'" filter="general" />
<debug_text text="'Player ship: %s'.[$playerShip.knownname]" filter="general" />

<!-- Variables -->
<set_value name="$myVar" exact="42" />
<set_value name="$myVar" operation="add" exact="1" />

<!-- Signals (inter-cue communication) -->
<signal_cue cue="md.MyScript.SomeCue" />
<signal_cue_instantly cue="md.MyScript.SomeCue" param="$someData" />

<!-- Object manipulation -->
<create_ship name="$newShip" macro="macro.ship_arg_m_frigate_01_a_macro" zone="player.zone">
  <owner exact="faction.player" />
</create_ship>

<!-- Flow control -->
<do_if value="$condition">
  <!-- actions -->
</do_if>
<do_elseif value="$other" />
<do_else />

<do_all exact="$list.count" counter="$i">
  <!-- loop body -->
</do_all>

<do_any>
  <!-- randomly pick one action set -->
</do_any>
```

## Variables and expressions

MD uses a custom expression language (not XPath):

```xml
<!-- Variable types -->
<set_value name="$int" exact="42" />
<set_value name="$float" exact="3.14" />
<set_value name="$string" exact="'hello'" />
<set_value name="$bool" exact="true" />
<set_value name="$table" exact="table[]" />
<set_value name="$list" exact="[]" />

<!-- Property access -->
<set_value name="$name" exact="player.occupiedship.knownname" />
<set_value name="$credits" exact="player.money" />

<!-- String formatting -->
<debug_text text="'%s has %d credits'.[player.name, player.money]" />

<!-- Arithmetic -->
<set_value name="$result" exact="($a + $b) * 2" />

<!-- Comparison -->
<check_value value="$health gt 50" />
<check_value value="$target.owner == faction.player" />
```

## Text references

In-game text uses page/entry IDs: `{pageId,entryId}`. Custom mods should use high page IDs (e.g., 90001+) to avoid conflicts:

```xml
<set_value name="$text" exact="{90001,1}" />
```

The corresponding translation file goes in `t/0001-l044.xml` (language 44 = English).

## Cross-referencing other MD scripts

```xml
<!-- Reference another script's cue -->
<event_cue_signalled cue="md.Setup.Start" />

<!-- Signal another mod's cue -->
<signal_cue cue="md.OtherMod.HandleEvent" param="$data" />
```

## Base game MD scripts (v9.00)

Notable scripts for reference:

| Script | Purpose |
|--------|---------|
| `md/setup.xml` | Game initialization -- fires `md.Setup.Start` that many scripts wait on |
| `md/factionlogic.xml` | Faction AI decision-making |
| `md/factionlogic_economy.xml` | Faction economic behavior |
| `md/diplomacy.xml` | Diplomatic relations system |
| `md/genericmissions.xml` | Mission generation framework |
| `md/encounters.xml` | Random encounter spawning |
| `md/faction_relations.xml` | Faction relation change handling |

---
