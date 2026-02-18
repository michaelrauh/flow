---
title: No Spatial Indexing for Collision Detection
labels: priority: medium, type: scalability
---

**Type:** Scalability  
**Severity:** Medium  
**Files:** `movement_resolver.py`, `water_pruner.py`

### Problem
Collision detection checks iterate through all entities:
- Wall checks: O(1) with set, but proposals check all water cells
- Pruning: Flood-fill visits all reachable cells
- Movement resolution: Iterates all movers for each target

For very large grids (100x100+) with many water cells, performance degrades linearly.

### Current Complexity
- `build_proposals()`: O(n) where n = water cells
- `group_targets()`: O(n)
- `_select_edges()`: O(n * m) where m = average movers per target
- `WaterPruner.prune()`: O(reachable cells)

### Suggested Solution
For future scalability:
- Consider spatial hashing or grid-based partitioning for very large levels
- Current performance is acceptable for puzzle-game level sizes
- Document expected grid size limits

---

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
