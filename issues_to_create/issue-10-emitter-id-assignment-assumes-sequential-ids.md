---
title: Emitter ID Assignment Assumes Sequential IDs
labels: priority: low, type: extensibility
---

**Type:** Extensibility / Robustness  
**Severity:** Low  
**File:** `levels.py:181`, `game.py:70`

### Problem
Emitter IDs are assigned sequentially:

```python
# levels.py
emitters.append(Emitter(len(emitters), x, y, dx, dy))

# game.py
self.next_emitter_id = (max((e.id for e in self.emitters), default=-1) + 1)
```

Issues:
- If emitters are removed, IDs can become sparse
- Color assignment uses `eid * 0.61803...` which works but could collide
- No ID recycling (unbounded growth in long sessions)

### Suggested Solution
- Consider UUID-based IDs for future serialization
- Or implement ID pool with recycling
- Document ID semantics and limits

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
