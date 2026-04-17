---
title: "Scaffolding Functions"
layout: default
parent: "Python API"
nav_order: 7
---

# Scaffolding Functions
## scaffold_project

Create a new mod project from the extension_poc template.

```python
from x4_catalog import scaffold_project

project_dir = scaffold_project(
    "my_mod",
    author="Your Name",
    description="A custom X4 mod",
    game_version=900,
    repo="youruser/my_mod",
    init_git=True,
)
print(f"Created project at {project_dir}")
```

**Signature:**

```python
def scaffold_project(
    mod_id: str,
    *,
    output_dir: Path | None = None,
    author: str | None = None,
    description: str | None = None,
    game_version: int = 900,
    repo: str | None = None,
    init_git: bool = False,
) -> Path: ...
```

Returns the path to the created project directory. Raises `FileExistsError` if the output directory already exists and is non-empty. Raises `ValueError` if `mod_id` is invalid.

## scaffold_ware

Generate boilerplate for a trade ware (Tier 1 -- no macro needed).

```python
from x4_catalog import scaffold_ware

files = scaffold_ware(
    "quantum_tubes",
    "Quantum Tubes",
    Path("./src"),
    group="hightech",
    price_avg=5000,
    volume=10,
)
# files = ["libraries/wares.xml", "t/0001-l044.xml"]
```

**Signature:**

```python
def scaffold_ware(
    ware_id: str,
    name: str,
    output_dir: Path,
    *,
    description: str = "",
    group: str = "",
    transport: str = "container",
    volume: int = 1,
    tags: str = "container economy",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

Returns a list of generated file paths relative to `output_dir`.

## scaffold_equipment

Clone an existing equipment item and generate all required files (Tier 2).

```python
from x4_catalog import scaffold_equipment

files = scaffold_equipment(
    "shield_gen_m_custom_01_macro",
    "Custom Shield",
    Path("./src"),
    clone_from="shield_gen_m_standard_01_mk1_macro",
    db_path=Path("./game.db"),
)
```

**Signature:**

```python
def scaffold_equipment(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Path | str | None = None,
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

## scaffold_ship

Clone an existing ship macro to create a new ship (Tier 3).

```python
from x4_catalog import scaffold_ship

files = scaffold_ship(
    "ship_my_s_fighter_01_a_macro",
    "Custom Fighter",
    Path("./src"),
    clone_from="ship_arg_s_fighter_01_a_macro",
    db_path=Path("./game.db"),
    size="s",
    price_avg=100000,
)
```

**Signature:**

```python
def scaffold_ship(
    macro_id: str,
    name: str,
    output_dir: Path,
    *,
    clone_from: str = "",
    db_path: Path | str | None = None,
    size: str = "s",
    description: str = "",
    price_min: int = 0,
    price_avg: int = 0,
    price_max: int = 0,
    page_id: int = 90001,
) -> list[str]: ...
```

Returns a list of generated file paths relative to `output_dir`. Note that creating a new ship also requires a component XML and 3D model -- see the generated `README_SHIP.md` for details.

---
