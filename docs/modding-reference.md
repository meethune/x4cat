---
title: "X4 Modding Reference"
layout: default
nav_order: 6
---

# X4: Foundations Modding Reference

A comprehensive reference for developing X4: Foundations mods (extensions). Compiled from Egosoft's official documentation, game file analysis (v9.00), and community resources.

**Official resources:**
- [Egosoft Modding Support Wiki](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/) -- canonical reference for all modding topics
- [Extensions Guide](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/Extensions/) -- extension structure and `content.xml`
- [XML Diff Patching](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/XML%20Diff%20Patching/) -- how to modify base game XML without replacing files
- [Mission Director Guide](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/) -- MD scripting (shared with X Rebirth)
- [Egosoft Modding Forum](https://forum.egosoft.com/viewforum.php?f=181) -- official community forum for X4 modding
- [Egosoft Forum -- Tools, Tutorials & Resources Index](https://forum.egosoft.com/viewtopic.php?f=181&t=402382) -- curated index of community tools

**Community resources:**
- [Roguey X4 Modding Guides](https://roguey.co.uk/x4/help/) -- tutorials for common mod types
- [Nexus Mods X4](https://www.nexusmods.com/x4foundations) -- community mod repository (1,500+ mods)
- [Getting into X4 modding on Linux](https://beko.famkos.net/2021/05/01/getting-into-x4-foundations-modding-on-linux/) -- Linux-specific tutorial
- [h2odragon's HOWTO-hackx4f](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/ScriptingMD/Community%20Guides/h2odragon's%20HOWTO-hackx4f/) -- practical walkthrough on the Egosoft wiki

**Tools:**
- [x4cat](https://github.com/meethune/x4cat) -- Linux/Python catalog tool (this project)
- [extension_poc](https://github.com/meethune/extension_poc) -- mod template with build pipeline
- [X4CodeComplete](https://www.nexusmods.com/x4foundations/mods/1721) -- VS Code extension for X4 XML autocompletion
- [X4-XMLDiffAndPatch](https://github.com/chemodun/X4-XMLDiffAndPatch) -- diff generation and patch application
- [X4 Customizer](https://github.com/bvbohnen/X4_Customizer) -- programmatic modding framework with GUI
- [WareGen](https://github.com/MattMcFarland/waregen) -- CLI tool for generating ware XML boilerplate

**Example mods (good learning resources):**
- [Genesis Signal](https://github.com/Vectorial1024/v1024_genesis_signal) -- clean MD game-start event detection
- [DeadAir Scripts](https://github.com/DeadAirRT/deadair_scripts) -- AI script modifications
- [kuertee UI Extensions](https://github.com/kuertee/x4-mod-ui-extensions) -- Lua UI callback system
- [sn_mod_support_apis](https://github.com/bvbohnen/x4-projects/tree/master/extensions/sn_mod_support_apis) -- MD-to-Lua bridging

---

## Table of Contents

1. [Extension Structure](#1-extension-structure)
2. [Catalog System (.cat/.dat)](#2-catalog-system-catdat)
3. [XML Diff Patching](#3-xml-diff-patching)
4. [Mission Director (MD) Scripts](#4-mission-director-md-scripts)
5. [AI Scripts](#5-ai-scripts)
6. [Libraries (Game Data XML)](#6-libraries-game-data-xml)
7. [Localization (Translation Files)](#7-localization-translation-files)
8. [UI / Lua Scripting](#8-ui--lua-scripting)
9. [Maps, Components, and Macros](#9-maps-components-and-macros)
10. [XSD Schemas](#10-xsd-schemas)
11. [In-Game Reference Files](#11-in-game-reference-files)
12. [Build Workflow with x4cat](#12-build-workflow-with-x4cat)
13. [Debugging](#13-debugging)
14. [Common Modding Recipes](#14-common-modding-recipes)
15. [File Type Reference](#15-file-type-reference)
16. [Signature Files](#16-signature-files)
17. [Common Pitfalls](#17-common-pitfalls)

---

## 1. Extension Structure

Every X4 mod is an **extension** -- a directory placed in `<X4 install>/extensions/<mod_id>/`.

### Minimum viable extension

```
extensions/my_mod/
  content.xml          -- Required. Extension manifest (always a loose file, never packed).
```

### Typical mod directory

```
extensions/my_mod/
  content.xml          -- Manifest
  ext_01.cat           -- Packed catalog index
  ext_01.dat           -- Packed catalog data
  md/                  -- Or packed inside ext_01.cat/dat
  aiscripts/
  libraries/
  t/
  ...
```

Mod files can be either **loose files** on disk or **packed into .cat/.dat catalogs**. Catalogs are preferred for distribution as they are faster to load and match the game's native format.

### content.xml

The extension manifest. X4 reads this as a loose file to determine whether and how to load the extension.

```xml
<?xml version="1.0" encoding="utf-8"?>
<content id="my_mod"
         version="100"
         name="My Mod Name"
         description="What this mod does"
         author="Your Name"
         date="2026-04-14"
         enabled="1"
         save="0">
  <!-- Minimum base game version required -->
  <dependency version="900" />

  <!-- Optional: depend on another extension (controls load order) -->
  <dependency id="ego_dlc_boron" version="100" optional="true" />
</content>
```

**Key attributes:**

| Attribute | Description |
|-----------|-------------|
| `id` | Unique identifier. Must match the directory name. Convention: lowercase, underscores. |
| `version` | Integer version number. Used for dependency checks. |
| `name` | Human-readable name shown in the Extension Manager. |
| `description` | Shown in the Extension Manager. |
| `enabled` | `"1"` to enable by default, `"0"` to disable. Users can toggle in-game. |
| `save` | `"1"` if the mod affects save games (most gameplay mods), `"0"` for cosmetic/UI-only. |
| `sync` | `"true"` if the mod must be synced in multiplayer Ventures. Usually `"false"`. |
| `date` | Publication date (informational). |

**Dependency element:**

| Attribute | Description |
|-----------|-------------|
| `version` | When no `id`: minimum base game version. When with `id`: minimum extension version. |
| `id` | Extension ID to depend on. Omit for base game dependency. |
| `optional` | `"true"` -- no error if missing. Controls load order only. |

### Load order

1. Base game catalogs (`01.cat` through `09.cat`) in numeric order
2. Extensions in dependency order, then alphabetical
3. Within each extension: `ext_01.cat` through `ext_NN.cat` in numeric order
4. Later files override earlier ones for the same virtual path

### Substitution catalogs

Extensions can use `subst_NN.cat` to override **base game** files directly (rather than adding extension-local files). In practice, DLCs do not use these -- `ext_NN.cat` with diff patching is the standard approach.

### Important rules

- MD script filenames in `md/` **must be lowercase** or X4 will silently ignore them.
- The extension directory name **must match** the `id` attribute in `content.xml`.
- Translation file page IDs must be globally unique across all loaded mods.
- Use `-prefersinglefiles` as a launch option during development to skip catalog packing and use loose files directly.
- If your mod diff-patches a DLC file, declare that DLC as a dependency in `content.xml`.

---

## 2. Catalog System (.cat/.dat)

X4 uses a simple archive format: a `.cat` text index paired with a `.dat` binary blob.

### .cat format

Each line in a `.cat` file describes one entry:

```
<filepath> <size> <unix_mtime> <md5hex>
```

- **filepath** -- virtual path (may contain spaces; last 3 fields are always fixed)
- **size** -- file size in bytes
- **unix_mtime** -- Unix timestamp (seconds since epoch)
- **md5hex** -- MD5 checksum of the file content (32 hex chars)

Example:

```
libraries/wares.xml 790216 1775564527 1df31b1302a8db514139e40d6f975f30
md/diplomacy.xml 510865 1775564527 a553805a63d9e37cf5524907a11ef9cd
assets/some folder/file.xmf 456 888888 00112233445566778899aabbccddeeff
```

### .dat format

The `.dat` file stores file contents consecutively in the same order as `.cat` lines. No headers, no separators -- just raw bytes back-to-back. The offset of each file is computed by summing the sizes of all preceding entries.

### Naming conventions

| Pattern | Scope | Example |
|---------|-------|---------|
| `NN.cat` | Base game | `01.cat`, `02.cat`, ..., `09.cat` |
| `ext_NN.cat` | Extension-local | `ext_01.cat`, `ext_02.cat` |
| `subst_NN.cat` | Base game override | `subst_01.cat` |
| `*_sig.cat` | Signature catalogs | `01_sig.cat` (Egosoft DRM, ignored by mods) |
| `ext_vNNN.cat` | Version-specific | `ext_v610.cat` (loaded only on game version >= 6.10) |

### Override semantics

When multiple catalogs contain the same virtual path, the **last one loaded wins**. This means:
- `02.cat` overrides `01.cat` for the same path
- `ext_02.cat` overrides `ext_01.cat`
- Extension catalogs override base game catalogs
- This is how mods replace game files without modifying originals

### Base game catalogs (v9.00)

| Catalog | Index | Data | Content |
|---------|-------|------|---------|
| 01 | 12 MB (90,977 entries) | 10 GB | Assets (models, textures, animations, audio) |
| 02 | 221 KB | 850 MB | Additional assets |
| 03 | 31 MB | 5.8 GB | More assets (textures, models) |
| 04 | 13 KB | 848 MB | Large asset files |
| 05 | 318 KB | 198 MB | Mixed content |
| 06 | 51 KB | 2.8 MB | Shaders, scripts |
| 07 | 45 KB | 25 MB | Music, effects |
| 08 | 72 KB | 51 MB | UI, scripts, libraries |
| 09 | 1.1 KB | 99 MB | Translation files |

### Working with catalogs using x4cat

```bash
# List files in game install
x4cat list "/path/to/X4 Foundations"

# List with filtering
x4cat list "/path/to/X4 Foundations" -g 'md/*.xml'
x4cat list "/path/to/X4 Foundations" --include '^libraries/' --exclude '\.xsd$'

# Extract files
x4cat extract "/path/to/X4 Foundations" -o ./unpacked -g 'libraries/wares.xml'

# Extract from a DLC extension
x4cat extract "/path/to/X4 Foundations/extensions/ego_dlc_boron" -o ./boron -p ext_

# Pack mod files into a catalog
x4cat pack ./src -o ./dist/ext_01.cat
```

---

## 3. XML Diff Patching

The most important modding technique. Instead of replacing entire game XML files (which breaks compatibility with other mods and game updates), you write **diff patches** that surgically modify specific elements.

**Reference:** [XML Diff Patching Wiki](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/XML%20Diff%20Patching/)

### How it works

When X4 loads a file like `libraries/wares.xml`, it first loads the base game version, then applies any diff patches found in extensions. A diff patch is an XML file with the **same virtual path** as the file it modifies, but with `<diff>` as the root element instead of the original root.

### Diff patch operations

The diff system supports three operations, selected via XPath in the `sel` attribute:

#### Add

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

#### Replace

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

#### Remove

```xml
<diff>
  <!-- Remove an element -->
  <remove sel="/wares/ware[@id='energycells']" />

  <!-- Remove an attribute -->
  <remove sel="/wares/ware[@id='energycells']/@tags" />
</diff>
```

### Conditional patching

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

### Silent patching

Add `silent="true"` to suppress errors when the XPath does not match (useful for optional patches):

```xml
<replace sel="/wares/ware[@id='might_not_exist']/@value" silent="true">42</replace>
```

### Multi-element selection (msel)

X4 extends the diff format with an `msel` attribute that allows matching multiple elements in a single operation:

```xml
<!-- Modify multiple wares at once -->
<replace sel="//ware" msel="/wares/ware[@id='energycells'] | /wares/ware[@id='water']" />
```

### XPath reference for diff patches

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

### Important notes

- The diff file must have the **exact same virtual path** as the file it patches
- The root element must be `<diff>`, not the original root element
- Multiple mods can diff-patch the same file -- they are applied in load order
- If a `sel` XPath does not match and `silent` is not set, X4 logs an error
- **Diff patching only works with extension catalogs (`ext_NN.cat`), not substitution catalogs**

### Generating and validating diff patches with x4cat

```bash
# Generate a diff from two XML files
x4cat xmldiff --base original.xml --mod modified.xml -o diff_patch.xml

# Validate all diff patches against the game
x4cat validate-diff "/path/to/X4 Foundations" ./src
```

### XSD schema for diff

The game ships a formal schema at `libraries/diff.xsd` defining the valid operations, XPath syntax, and attributes. Extract it for reference:

```bash
x4cat extract "/path/to/X4 Foundations" -o ./schemas -g 'libraries/diff.xsd'
```

---

## 4. Mission Director (MD) Scripts

MD scripts drive game logic: missions, faction behavior, event responses, UI triggers, and more. They are XML-based state machines using a cue/condition/action pattern.

**Reference:** [Mission Director Guide](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/)

### Location

- Base game: `md/*.xml`
- Extensions: `md/*.xml` (in catalog or loose)
- Schema: `libraries/md.xsd` (includes `libraries/common.xsd` -- 45K lines total)

### Basic structure

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

### Key concepts

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

### Common events

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

### Common actions

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

### Variables and expressions

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

### Text references

In-game text uses page/entry IDs: `{pageId,entryId}`. Custom mods should use high page IDs (e.g., 90001+) to avoid conflicts:

```xml
<set_value name="$text" exact="{90001,1}" />
```

The corresponding translation file goes in `t/0001-l044.xml` (language 44 = English).

### Cross-referencing other MD scripts

```xml
<!-- Reference another script's cue -->
<event_cue_signalled cue="md.Setup.Start" />

<!-- Signal another mod's cue -->
<signal_cue cue="md.OtherMod.HandleEvent" param="$data" />
```

### Base game MD scripts (v9.00)

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

## 5. AI Scripts

AI scripts control individual ship/entity behavior (orders, combat, trading, mining). More granular than MD scripts -- they operate at the entity level rather than the game level.

### Location

- Base game: `aiscripts/*.xml`
- Schema: `libraries/aiscripts.xsd` (includes `libraries/common.xsd`)

### Basic structure

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

### Key elements

| Element | Description |
|---------|-------------|
| `<params>` | Input parameters the script accepts when invoked |
| `<interrupts>` | Interrupt handlers -- respond to events mid-execution |
| `<init>` | One-time initialization when the script starts |
| `<attention>` | Main logic block. `min` attribute sets minimum attention level. |
| `<actions>` | Sequential action list within an attention block |

### Attention levels

AI scripts only execute when their entity has sufficient attention from the game engine:

| Level | Description |
|-------|-------------|
| `visible` | Entity is on-screen |
| `known` | Entity is in a known sector |
| `unknown` | Entity exists anywhere (lowest requirement) |

### Interrupt handlers

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

### The `this` object

Inside an AI script, `this` refers to the entity running the script:

```xml
<set_value name="$myShip" exact="this.ship" />
<set_value name="$myZone" exact="this.zone" />
<set_value name="$myOwner" exact="this.ship.owner" />
```

### Base game AI scripts (v9.00)

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

## 6. Libraries (Game Data XML)

The `libraries/` directory contains the game's core data definitions -- the "database" of game objects, their properties, and relationships.

### Key library files

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

### Modding libraries with diff patches

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

### Ware text references

Text in wares uses the format `{pageId,entryId}`:
- `name="{20201,101}"` -- references page 20201, entry 101 in translation files
- Custom mods should use page IDs 90000+ to avoid conflicts

### Production chain example

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

## 7. Localization (Translation Files)

### Location

Translation files live in `t/` with the naming pattern `NNNN-lLLL.xml`:
- `NNNN` -- page group number (e.g., `0001` for core game text)
- `LLL` -- language code

### Language codes

| Code | Language |
|------|----------|
| 7 | Russian |
| 33 | French |
| 34 | Spanish |
| 39 | Italian |
| 42 | Czech |
| 44 | English |
| 48 | Polish |
| 49 | German |
| 55 | Portuguese |
| 81 | Japanese |
| 82 | Korean |
| 86 | Simplified Chinese |
| 88 | Traditional Chinese |

### File format

```xml
<?xml version="1.0" encoding="utf-8"?>
<language id="44">
  <page id="90001" title="My Mod" descr="Custom mod strings" voice="no">
    <t id="1">My Custom Ware</t>
    <t id="2">A custom ware added by my mod</t>
    <t id="100">Mission briefing text here</t>
  </page>
</language>
```

### Usage in other XML

Reference text with `{pageId,entryId}`:

```xml
<ware id="my_ware" name="{90001,1}" description="{90001,2}" />
```

### In MD scripts

```xml
<set_value name="$text" exact="{90001,1}" />
<debug_text text="'Ware name: ' + {90001,1}" />
```

### Best practices

- Use page IDs **90000+** for custom mods to avoid conflicts with base game and other mods
- Always provide at least English (`l044`) translations
- Translation files can be diff-patched to add pages to existing files, or provided as new files

---

## 8. UI / Lua Scripting

X4's UI system is built with Lua scripts and XML layout definitions.

### Location

- `ui/addons/<addon_name>/` -- each UI addon is a self-contained directory
- Lua scripts (`.lua`) handle logic
- XML files define menu structures

### Base game UI addons

| Addon | Purpose |
|-------|---------|
| `ego_detailmonitor` | Main game menus (map, encyclopedia, ship config, station config, etc.) |
| `ego_interactmenu` | Right-click context menus |
| `ego_gameoptions` | Game settings menus |
| `ego_chatwindow` | Chat/communication window |
| `ego_debuglog` | Debug log viewer |
| `ego_targetmonitor` | Target info display |

### Notable Lua files

| File | Size | Purpose |
|------|------|---------|
| `menu_map.lua` | 1.5 MB | The map interface -- largest single script |
| `menu_ship_configuration.lua` | 521 KB | Ship loadout/configuration |
| `menu_station_configuration.lua` | 303 KB | Station building |
| `menu_playerinfo.lua` | 335 KB | Player info/empire overview |
| `menu_encyclopedia.lua` | 192 KB | In-game encyclopedia |
| `menu_diplomacy.lua` | 196 KB | Diplomatic relations |

### Modding UI

UI modding is significantly more constrained than XML modding:

- Lua files must use the **`.xpl` extension** (not `.lua`)
- UI XML files (`ui.xml`) **cannot be diff-patched** -- they must be fully replaced
- Replaced UI files must be packed in **`subst_NN.cat`** catalogs (which replace base game files), making them fragile across game updates
- Only **one mod** can replace a given Lua function -- multiple mods touching the same UI element will conflict

### kuertee's UI Extensions API

The community solution for multi-mod UI compatibility is [kuertee's UI Extensions](https://www.nexusmods.com/x4foundations/mods/552) ([GitHub](https://github.com/kuertee/x4-mod-ui-extensions)). It provides a callback-based system:

1. Get a pointer to the base game menu
2. Register a callback function
3. Write changes in the callback
4. Return what the callback expects

This allows multiple mods to modify the same UI element without conflict.

### Protected UI Mode

Introduced in X4 7.0/7.5, Protected UI Mode (`uisafemode` in config) is a security sandbox for the Lua UI layer. It prevents mods from executing arbitrary Lua code. Found in-game under **Settings > Extensions**.

**When enabled (default), it blocks:**
- Loading custom Lua files via mods
- Lua `require()` calls to non-whitelisted modules (only `ffi` is whitelisted)
- Named pipe connections for external program communication
- The legacy `Lua_Loader` MD signal method (`<raise_lua_event name="'Lua_Loader.Load'" .../>`)

**What it does NOT affect:**
- Pure XML-based MD scripts -- completely unaffected
- AI scripts (XML) -- completely unaffected
- Game data XML modifications (wares, ships, etc.) -- completely unaffected

**For mod developers:**
- The new recommended approach is to declare Lua files in `ui.xml` (loaded alongside base-game Lua), rather than the legacy MD signal method
- [SirNukes Mod Support APIs](https://github.com/bvbohnen/x4-projects/blob/master/extensions/sn_mod_support_apis/Readme.md) patches `require()` to allow mod Lua registration in protected mode via `Register_Require_Response`
- Disabling Protected UI Mode also disables some X4 online features (Ventures, Timelines leaderboards)

**For end users installing Lua mods:** disable Protected UI Mode via Settings > Extensions, then restart.

**References:**
- [Egosoft Forum: Protected UI mode discussion](https://forum.egosoft.com/viewtopic.php?t=469392)
- [SirNukes Mod Support APIs](https://github.com/bvbohnen/x4-projects/blob/master/extensions/sn_mod_support_apis/Readme.md)
- [kuertee UI Extensions](https://github.com/kuertee/x4-mod-ui-extensions/blob/master/README.md)

---

## 9. Maps, Components, and Macros

### Index files

Two master index files define the game's object registry:

- `index/components.xml` (318 KB) -- maps component names to XML definition files
- `index/macros.xml` (358 KB) -- maps macro names to XML definition files

These are how X4 resolves references like `macro.ship_arg_m_frigate_01_a_macro` -- it looks up the macro name in `index/macros.xml` to find the definition file.

### Components vs. Macros

- **Components** -- define the structural template of an object (mesh, collision, connections)
- **Macros** -- define a specific instance/variant of a component with concrete values (stats, loadouts)

Example: one frigate component can have multiple macros (Argon variant, Paranid variant, etc.)

### Map structure

Maps define the galaxy layout:

```
maps/
  xu_ep2_universe_macro.xml     -- main galaxy definition
  *_galaxy_macro.xml            -- individual galaxy definitions
```

### Index file registration

**Every new macro and component must be registered in the index files** or the game will not know they exist. This is the most common reason new content fails to appear.

For a new ship macro:

```xml
<!-- index/macros.xml diff patch -->
<diff>
  <add sel="/index">
    <entry name="my_ship_macro" value="extensions\my_mod\assets\units\size_m\macros\my_ship_macro" />
  </add>
</diff>
```

### Asset macro paths

When adding new content, macros go in standardized paths:

| Content type | Macro path |
|-------------|------------|
| Small ships (S) | `assets/units/size_s/macros/` |
| Medium ships (M) | `assets/units/size_m/macros/` |
| Large ships (L) | `assets/units/size_l/macros/` |
| Extra-large ships (XL) | `assets/units/size_xl/macros/` |
| Shields | `assets/props/SurfaceElements/macros/` |
| Weapons | `assets/props/WeaponSystems/<type>/macros/` |
| Turrets | `assets/props/WeaponSystems/integratedturrets/macros/` |

### Assets

The `assets/` directory tree contains 3D models, textures, animations, and other binary content:

```
assets/
  characters/     -- character models and animations
  environments/   -- environment/station meshes
  fx/             -- visual effects
  props/          -- prop objects (shields, weapons, turrets)
  ships/          -- ship models
  units/          -- unit macros by size class
  ...
```

Asset files use Egosoft's proprietary formats (`.xmf`, `.xpm`, `.xac`, `.xsm`).

---

## 10. XSD Schemas

X4 ships 41 XSD schema files that formally define the structure of its XML files. These are invaluable for validation during mod development.

### Extracting schemas

```bash
x4cat extract "/path/to/X4 Foundations" -o ./schemas -g '*.xsd'
```

### Schema hierarchy

```
md/md.xsd                    -- includes ../libraries/md.xsd
aiscripts/aiscripts.xsd      -- includes ../libraries/aiscripts.xsd
libraries/md.xsd              -- includes common.xsd
libraries/aiscripts.xsd       -- includes common.xsd
libraries/common.xsd          -- base types and expressions (40K lines)
libraries/diff.xsd            -- diff patching operations
libraries/libraries.xsd       -- library file structures
```

### Key schemas

| Schema | Lines | Purpose |
|--------|-------|---------|
| `libraries/common.xsd` | 40,572 | Base types, expression language, variables |
| `libraries/md.xsd` | 4,919 | Mission Director elements and attributes |
| `libraries/aiscripts.xsd` | -- | AI script elements |
| `libraries/diff.xsd` | -- | Diff patch operations (add/replace/remove) |
| `libraries/parameters.xsd` | -- | Game parameter definitions |
| `libraries/libraries.xsd` | -- | Library XML structures |

### Validation

Full XSD validation is slow (~70 seconds) due to the size of `common.xsd`. For development, use structural checks (correct root element, required attributes) and reserve full XSD validation for pre-release verification.

```bash
# Fast: structural validation
xmllint --noout src/md/*.xml

# Slow but thorough: full XSD validation
xmllint --schema schemas/md/md.xsd --noout src/md/my_script.xml
```

Or use the extension_poc template's `make schema-validate` target.

---

## 11. In-Game Reference Files

X4 ships interactive reference files that document all available script operations, properties, and keywords. Extract these for offline use:

```bash
x4cat extract "/path/to/X4 Foundations" -o ./reference -g '*.html'
x4cat extract "/path/to/X4 Foundations" -o ./reference -g 'libraries/scriptproperties.*'
```

### Available references

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

## 12. Build Workflow with x4cat

### Recommended project structure

```
my_mod/
  content.xml          -- Extension manifest (loose file)
  src/                 -- Mod files (packed into catalog)
    md/                -- Mission Director scripts
    aiscripts/         -- AI scripts
    libraries/         -- Library diff patches
    t/                 -- Translation files
  dist/                -- Build output
  schemas/             -- Extracted XSD schemas (gitignored)
  tests/               -- Validation tests
  Makefile
  pyproject.toml       -- uv project with x4cat dev dependency
```

Use `x4cat init <mod_id>` to generate this structure automatically. See the [mod project tutorial](tutorials/mod-project) for a walkthrough.

### Build commands

```bash
# Pack mod files into a catalog
x4cat pack ./src -o ./dist/ext_01.cat
cp content.xml ./dist/

# Or use the diff workflow for iterative development
x4cat diff --base ./base --mod ./src -o ./dist/ext_01.cat
```

### Installation

Copy the contents of `dist/` to `<X4 install>/extensions/<mod_id>/`.

The directory must contain at minimum `content.xml`. If using catalogs, also `ext_01.cat` and `ext_01.dat`.

---

## 13. Debugging

### Debug log

X4 writes a debug log to:
- **Windows:** `%USERPROFILE%\Documents\Egosoft\X4\<save_id>\debug.log`
- **Linux:** `~/.config/EgoSoft/X4/<save_id>/debug.log`

### Launch parameters

Add these to the X4 launch options (Steam: right-click > Properties > Launch Options):

```
-debug all -logfile debuglog.txt -scriptlogfiles
```

| Parameter | Effect |
|-----------|--------|
| `-debug all` | Enable all debug output categories |
| `-logfile debuglog.txt` | Write debug output to a named file |
| `-scriptlogfiles` | Generate per-script log files for MD/AI scripts |
| `-prefersinglefiles` | Load loose files instead of catalogs (skip packing during development) |

### debug_text in MD/AI scripts

```xml
<debug_text text="'My debug message'" filter="general" />
<debug_text text="'Value: %s'.[$myVar]" filter="general" chance="100" />
```

The `chance` attribute (0-100) controls how often the message is logged. Use `chance="$DebugChance"` with a configurable variable to easily toggle verbosity.

### Debug filters

Use the `filter` attribute to categorize debug output:
- `general` -- general purpose
- `error` -- errors
- `scripts` / `scripts_verbose` -- script execution
- `economy_verbose` -- economic simulation
- `combat` -- combat events
- `fileio` -- file loading (shows all missing signature warnings)
- `savegame` -- save/load operations

### In-game debug tools

- **Debug Log Viewer** -- accessible in-game (Controls > General > Open Debug Log)
- **Extension Manager** -- shows loaded extensions and their status

### Common errors

| Error | Cause |
|-------|-------|
| `Could not find signature file` | Expected for mods -- harmless, Egosoft-only DRM |
| `Diff patch: no match for sel` | XPath in diff patch does not match target -- check selector |
| `XML parse error` | Malformed XML in mod file |
| `Unknown cue reference` | MD script references a cue that does not exist |
| `Macro not found` | Referenced macro is not registered in `index/macros.xml` |

---

## 14. Common Modding Recipes

### Add a new ware

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

### Modify a game value

Diff patch `libraries/wares.xml` to change energy cell price:

```xml
<diff>
  <replace sel="/wares/ware[@id='energycells']/price/@max">100</replace>
</diff>
```

### Add an MD script that runs on game start

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

### Add NPC jobs (ship spawns)

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

### Add a new ship to a faction's wharves

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

## 15. File Type Reference

### File types in game archives (v9.00)

| Extension | Count | Description |
|-----------|-------|-------------|
| `.ogg` | 292,881 | Audio (Ogg Vorbis) -- music, sound effects, voice |
| `.xpm` | 72,427 | Egosoft packed texture format |
| `.xmf` | 40,157 | Egosoft mesh format (3D models) |
| `.jcs` | 31,756 | Compressed data (JSON) |
| `.gz` | 10,884 | Gzipped data (textures, shaders) |
| `.xml` | 6,391 | Game data, scripts, configuration |
| `.ANI` / `.ani` | 2,448 | Animation files |
| `.wav` | 1,678 | Audio (WAV) |
| `.xsm` | 1,116 | Egosoft skeletal mesh animation |
| `.xac` | 471 | Egosoft actor format |
| `.psb` | 418 | Particle system binary |
| `.glsl` | 290 | OpenGL shader source |
| `.dds` | 93 | DirectDraw Surface textures |
| `.lua` | 81 | Lua scripts (UI) |
| `.xsd` | 41 | XML Schema definitions |
| `.xpl` | 81 | Compiled Lua (proprietary) |
| `.dae` | 19 | COLLADA 3D models |

### Most commonly modded file types

- `.xml` -- scripts, libraries, configs (can be diff-patched)
- `.lua` -- UI scripts (must be replaced entirely or function-patched)
- `.ogg` -- audio replacements
- `.dds` -- texture replacements

---

## 16. Signature Files

X4 uses RSA signature files for DRM/integrity verification of official content.

### Format

- Every official file has a corresponding `.sig` file
- Signature catalogs: `*_sig.cat`/`*_sig.dat` contain `.sig` entries for catalog-packed files
- Each `.sig` file is exactly **1024 bytes** (8192-bit RSA signature)
- Signed with Egosoft's private key, verified with their public key embedded in the game

### Impact on mods

- Mods **cannot and do not need to** generate signature files
- The game logs `Could not find signature file` for unsigned mod files -- this is **expected and harmless**
- The error appears once per session, then is suppressed (or use `fileio` debug filter for all)
- This does not affect mod functionality in any way

---

## 17. Common Pitfalls

Recurring issues across all modding topics, compiled from community experience:

1. **Uppercase filenames** -- MD scripts in `md/` must be lowercase. X4 silently ignores files that do not match expected casing. On Linux, all paths are case-sensitive.

2. **Full file replacement instead of diff patching** -- breaks on every game update and conflicts with other mods. Always use `<diff>` patches for library files.

3. **Missing index registration** -- the number one reason new content "does not exist." Every new macro needs `index/macros.xml`; every new component needs `index/components.xml`.

4. **Forgetting `&quot;` escaping in XPath** -- attribute values in diff patch `sel` XPath must use `&quot;` for quotes: `sel="//ware[@id=&quot;energycells&quot;]"`.

5. **Line breaks in content.xml** -- use `&#10;` in description text, not `\n`.

6. **Silent diff patch failures** -- if a `sel` XPath does not match, X4 logs a warning but otherwise silently skips. Enable `-debug all` to see these. Use `x4cat validate-diff` to catch them before shipping.

7. **Version field is an integer** -- `version="100"` means version 1.00. Multiply by 100.

8. **Game updates break things** -- diff patches are more resilient than replacements, but any mod can break on major updates. Consider locking game versions for stable mod lists.

9. **Ware IDs must be lowercase** -- uppercase characters in ware IDs cause problems on case-sensitive filesystems.

10. **Mod placement** -- mods can go in two locations:
    - Game directory: `<X4 install>/extensions/`
    - User documents: `Documents/Egosoft/X4/extensions/`
    - Some features (like `subst` catalogs) only work from the game directory.

---

## Quick Reference Links

### Official

| Resource | URL |
|----------|-----|
| Egosoft Modding Wiki | [https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/) |
| Extensions Guide | [https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/Extensions/](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/Extensions/) |
| XML Diff Patching | [https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/XML%20Diff%20Patching/](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Modding%20Support/XML%20Diff%20Patching/) |
| Mission Director Guide | [https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/](https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/) |
| Egosoft Forum (Modding) | [https://forum.egosoft.com/viewforum.php?f=181](https://forum.egosoft.com/viewforum.php?f=181) |
| Forum Tools/Tutorials Index | [https://forum.egosoft.com/viewtopic.php?f=181&t=402382](https://forum.egosoft.com/viewtopic.php?f=181&t=402382) |

### Tools

| Tool | URL |
|------|-----|
| x4cat (catalog tool) | [https://github.com/meethune/x4cat](https://github.com/meethune/x4cat) |
| extension_poc (mod template) | [https://github.com/meethune/extension_poc](https://github.com/meethune/extension_poc) |
| X4-XMLDiffAndPatch | [https://github.com/chemodun/X4-XMLDiffAndPatch](https://github.com/chemodun/X4-XMLDiffAndPatch) |
| X4 Customizer | [https://github.com/bvbohnen/X4_Customizer](https://github.com/bvbohnen/X4_Customizer) |
| WareGen | [https://github.com/MattMcFarland/waregen](https://github.com/MattMcFarland/waregen) |
| X4CodeComplete (VS Code) | [https://www.nexusmods.com/x4foundations/mods/1721](https://www.nexusmods.com/x4foundations/mods/1721) |
| kuertee UI Extensions | [https://github.com/kuertee/x4-mod-ui-extensions](https://github.com/kuertee/x4-mod-ui-extensions) |

### Community and Learning

| Resource | URL |
|----------|-----|
| Nexus Mods (X4) | [https://www.nexusmods.com/x4foundations](https://www.nexusmods.com/x4foundations) |
| Steam Workshop (X4) | [https://steamcommunity.com/app/392160/workshop/](https://steamcommunity.com/app/392160/workshop/) |
| Roguey X4 Guides | [https://roguey.co.uk/x4/help/](https://roguey.co.uk/x4/help/) |
| Linux modding guide | [https://beko.famkos.net/2021/05/01/getting-into-x4-foundations-modding-on-linux/](https://beko.famkos.net/2021/05/01/getting-into-x4-foundations-modding-on-linux/) |
| Genesis Signal (example mod) | [https://github.com/Vectorial1024/v1024_genesis_signal](https://github.com/Vectorial1024/v1024_genesis_signal) |
| DeadAir Scripts (example mod) | [https://github.com/DeadAirRT/deadair_scripts](https://github.com/DeadAirRT/deadair_scripts) |
| sn_mod_support_apis | [https://github.com/bvbohnen/x4-projects/tree/master/extensions/sn_mod_support_apis](https://github.com/bvbohnen/x4-projects/tree/master/extensions/sn_mod_support_apis) |
