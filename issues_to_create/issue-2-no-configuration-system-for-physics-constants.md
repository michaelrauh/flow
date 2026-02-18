---
title: No Configuration System for Physics Constants
labels: priority: medium, type: extensibility, type: usability
---

**Type:** Extensibility / Usability  
**Severity:** Medium  
**Files:** `simulation_constants.py`, `simulation_engine.py`, `game.py`

### Problem
Physics parameters are hardcoded across multiple files:
- `STEP_MS = 120` (tick duration)
- `STATIONARY_DECAY_MS = 250` (water decay time)
- `GAME_SPEED = 5.0` (UI speed multiplier)

This prevents:
- Per-level difficulty tuning
- User-configurable simulation speed
- Testing with different parameters

### Current Code
```python
# simulation_constants.py
STEP_MS = 120
STATIONARY_DECAY_MS = 250

# game.py
GAME_SPEED = 5.0
```

### Suggested Solution
Create a configuration system (YAML/JSON or dataclass-based) that allows:
- Global defaults
- Per-level overrides
- Runtime modification

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
