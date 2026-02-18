---
title: prev_owner Dict Rebuilt Every Tick
labels: priority: medium, type: scalability, type: performance
---

**Type:** Scalability / Performance  
**Severity:** Low-Medium  
**File:** `movement_resolver.py:20`

### Problem
Every tick, `prev_owner` is rebuilt from scratch:

```python
self.prev_owner = {pos: cell.emitter_id for pos, cell in state.water.items()}
```

For large grids with many water cells, this creates unnecessary allocations and iterations every frame.

### Suggested Solution
Maintain `prev_owner` incrementally:
- Update only changed cells after each tick
- Or track ownership in the `SimulationState` directly
- Consider storing emitter_id directly in water dict key if frequently accessed

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
