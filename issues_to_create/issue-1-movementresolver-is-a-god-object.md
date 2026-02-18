---
title: MovementResolver is a God Object
labels: priority: high, type: extensibility, type: maintainability
---

**Type:** Extensibility / Maintainability  
**Severity:** Medium-High  
**File:** `movement_resolver.py`

### Problem
The `MovementResolver` class (231 lines) handles too many responsibilities:
- Spawning water from emitters
- Building movement proposals
- Grouping targets
- Collision detection and resolution
- Advancing water state
- Backpressure calculation

This violates the Single Responsibility Principle and makes the code:
- Difficult to test individual components
- Hard to extend with new movement behaviors
- Challenging to optimize specific phases

### Suggested Solution
Split into separate components:
- `WaterSpawner` - Handle emitter spawning logic
- `MovementProposer` - Build movement proposals
- `CollisionResolver` - Handle conflict resolution
- `WaterAdvancer` - Apply movements and age water

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
