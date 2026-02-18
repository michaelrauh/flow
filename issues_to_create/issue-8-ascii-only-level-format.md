---
title: ASCII-Only Level Format
labels: priority: medium, type: extensibility, type: usability
---

**Type:** Extensibility / Usability  
**Severity:** Low-Medium  
**File:** `levels.py`

### Problem
Levels are defined as ASCII strings:

```python
LEVEL_DENSE_WIDE = [
    "############################",
    "#>...............#........S#",
    "#>........................S#",
    "############################",
]
```

Limitations:
- Can't store metadata (author, difficulty, hints)
- No support for per-level physics config
- Limited character set (can't represent all entity types)
- Harder to create level editor exports

### Suggested Solution
Support additional formats:
- JSON/YAML for rich metadata
- Keep ASCII as human-readable editing format
- Add level metadata dataclass
- Create level export/import utilities

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
