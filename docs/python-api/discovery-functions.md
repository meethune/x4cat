---
title: "Discovery Functions"
layout: default
parent: "Python API"
nav_order: 5
---

# Discovery Functions
## inspect_asset

Look up an asset by ware ID, macro name, or component name. Tries ware first, then macro, then component.

```python
from x4_catalog import inspect_asset

result = inspect_asset("energycells", Path("./game.db"))
if result:
    print(result["ware_id"], result["price_avg"])
```

**Signature:**

```python
def inspect_asset(asset_id: str, db_path: Any) -> dict[str, Any] | None: ...
```

Returns a dict with all known information or `None` if not found.

## search_assets

Search across wares, macros, and components by case-insensitive substring match.

```python
from x4_catalog import search_assets

results = search_assets("fighter", Path("./game.db"), type_filter="macro")
for r in results:
    print(f"{r['type']:10s} {r['id']}")
```

**Signature:**

```python
def search_assets(
    term: str,
    db_path: Any,
    *,
    type_filter: str | None = None,
) -> list[dict[str, str]]: ...
```

Each result dict has keys: `id`, `type`, `path`, `detail`.

## extract_macro

Extract a macro file by ID, resolving its virtual path through the index.

```python
from x4_catalog import extract_macro

result = extract_macro(
    "ship_arg_s_fighter_01_a_macro",
    Path("./game.db"),
    Path("/path/to/X4 Foundations"),
    Path("./output"),
)
if result:
    print(f"Extracted to {result}")
```

**Signature:**

```python
def extract_macro(
    macro_id: str,
    db_path: Any,
    game_dir: Path,
    output_dir: Path,
) -> Path | None: ...
```

Returns the path to the extracted file, or `None` if the macro is not found.

---
