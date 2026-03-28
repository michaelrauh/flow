---
title: Direction Mappings Duplicated Across Files
labels: priority: medium, type: extensibility, type: maintainability
---

**Type:** Extensibility / Maintainability  
**Severity:** Low-Medium  
**Files:** `levels.py`, `simulation_constants.py`

### Problem
Direction mappings are defined in two places:

```python
# levels.py:150-156
DIRS = {
    "^": (0, -1),
    ">": (1, 0),
    "v": (0, 1),
    "<": (-1, 0),
}

# simulation_constants.py:3-8
WATER_DIR_CHAR = {
    (0, -1): "U",
    (1, 0): "R",
    (0, 1): "D",
    (-1, 0): "L",
}
```

This creates:
- Sync risk if directions change
- Confusion about which to use
- Harder to add diagonal movement support

### Suggested Solution
Consolidate into a single `directions.py` module with:
- Canonical direction definitions
- Direction utility functions (rotate left/right, opposite)
- Both char-to-tuple and tuple-to-char mappings

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
