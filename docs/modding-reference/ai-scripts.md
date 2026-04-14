---
title: "AI Scripts"
layout: default
parent: "X4 Modding Reference"
nav_order: 5
---

# AI Scripts

AI scripts control individual ship/entity behavior (orders, combat, trading, mining). More granular than MD scripts -- they operate at the entity level rather than the game level.

## Location

- Base game: `aiscripts/*.xml`
- Schema: `libraries/aiscripts.xsd` (includes `libraries/common.xsd`)

## Basic structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<aiscript name="my.custom.order"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:noNamespaceSchemaLocation="aiscripts.xsd">
  <params>
    <param name="target" required="true" type="object" />
    <param name="timeout" default="300" type="number" />
  </params>
  <interrupts>
    <handler ref="AttackHandler" />
    <handler ref="ScanHandler" />
  </interrupts>
  <init>
    <set_value name="$debugchance" exact="0" />
  </init>
  <attention min="unknown">
    <actions>
      <label name="start" />

      <run_script name="'move.generic'">
        <param name="destination" value="$target" />
      </run_script>

      <!-- AI script logic -->

      <label name="finish" />
    </actions>
  </attention>
</aiscript>
```

## Key elements

| Element | Description |
|---------|-------------|
| `<params>` | Input parameters the script accepts when invoked |
| `<interrupts>` | Interrupt handlers -- respond to events mid-execution |
| `<init>` | One-time initialization when the script starts |
| `<attention>` | Main logic block. `min` attribute sets minimum attention level. |
| `<actions>` | Sequential action list within an attention block |

## Attention levels

AI scripts only execute when their entity has sufficient attention from the game engine:

| Level | Description |
|-------|-------------|
| `visible` | Entity is on-screen |
| `known` | Entity is in a known sector |
| `unknown` | Entity exists anywhere (lowest requirement) |

## Interrupt handlers

```xml
<interrupts>
  <!-- Reference a library handler -->
  <handler ref="AttackHandler" />

  <!-- Inline handler -->
  <handler>
    <conditions>
      <event_object_attacked object="this.ship" />
    </conditions>
    <actions>
      <!-- respond to being attacked -->
    </actions>
  </handler>
</interrupts>
```

## The `this` object

Inside an AI script, `this` refers to the entity running the script:

```xml
<set_value name="$myShip" exact="this.ship" />
<set_value name="$myZone" exact="this.zone" />
<set_value name="$myOwner" exact="this.ship.owner" />
```

## Base game AI scripts (v9.00)

Key script families:

| Pattern | Purpose |
|---------|---------|
| `order.*.xml` | Player-assignable orders (trade, mine, patrol, etc.) |
| `fight.attack.*.xml` | Combat behaviors by ship class |
| `move.*.xml` | Movement/navigation |
| `interrupt.*.xml` | Interrupt handler libraries |
| `lib.*.xml` | Shared utility libraries |
| `engineer.*.xml` | Engineering/repair behaviors |
| `mining.*.xml` | Mining operations |

---
