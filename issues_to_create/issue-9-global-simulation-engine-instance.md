---
title: Global Simulation Engine Instance
labels: priority: low, type: extensibility, type: testability
---

**Type:** Testability / Extensibility  
**Severity:** Low  
**File:** `game.py:21`

### Problem
A global `_ENGINE` instance is used:

```python
_ENGINE = SimulationEngine()
```

Issues:
- Difficult to test game.py in isolation
- Can't run multiple simulations simultaneously
- State from one test can leak to another
- No dependency injection

### Suggested Solution
- Remove global `_ENGINE`
- Pass engine as constructor parameter to `WaterState`
- Or inject via dependency injection framework
- Consider factory pattern for engine creation

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
