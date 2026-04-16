---
title: "Conflict Detection"
layout: default
parent: "Python API"
nav_order: 6
---

# Conflict Detection
## check_conflicts

```python
from x4_catalog import check_conflicts

result = check_conflicts([Path("./my_mod"), Path("./other_mod")])
# result["conflicts"]     -- list of CONFLICT entries
# result["safe"]          -- list of SAFE overlaps (add+add)
# result["info"]          -- list of INFO overlaps
# result["files_checked"] -- number of shared files analyzed
```

```python
def check_conflicts(
    mod_dirs: list[Path],
) -> dict[str, Any]: ...
```

Compares diff patches across two or more mod directories. Classifies overlapping XPath selectors as CONFLICT (replace+replace, remove+modify), SAFE (add+add to same parent), or INFO (mixed operations).

---
