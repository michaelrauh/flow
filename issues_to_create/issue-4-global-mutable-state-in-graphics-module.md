---
title: Global Mutable State in Graphics Module
labels: priority: medium, type: scalability, type: testability
---

**Type:** Scalability / Testability  
**Severity:** Medium  
**File:** `graphics.py`

### Problem
Global sprite caches are never cleared:

```python
_WALL_SURFACE = None
_SINK_SURFACE_CACHE = {}
_EMITTER_SURFACE_CACHE = {}
_WATER_SURFACE_CACHE = {}
```

Issues:
- Memory grows unbounded with many unique emitter colors
- Cache not cleared between level loads (potential visual bugs)
- Makes unit testing difficult (state leaks between tests)
- Not thread-safe if multi-threaded rendering is added

### Suggested Solution
- Encapsulate caches in a `SpriteCache` class
- Add `clear()` method for level transitions
- Consider LRU cache with size limits
- Make cache injectable for testing

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
