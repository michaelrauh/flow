# Scalability and Extensibility Issues

This document outlines identified issues that affect the scalability and extensibility of the flow simulation codebase. Each section below represents a potential GitHub issue.

---

## Issue 1: MovementResolver is a God Object

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

## Issue 2: No Configuration System for Physics Constants

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

## Issue 3: Direction Mappings Duplicated Across Files

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

## Issue 4: Global Mutable State in Graphics Module

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

## Issue 5: prev_owner Dict Rebuilt Every Tick

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

## Issue 6: No Spatial Indexing for Collision Detection

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

## Issue 7: Hardcoded Entity Type System

**Type:** Extensibility  
**Severity:** Medium-High  
**Files:** Multiple

### Problem
The codebase only supports three entity types:
- **Walls** - Block flow
- **Emitters** - Spawn water
- **Sinks** - Absorb water

Adding new entities (pumps, valves, reservoirs, teleporters, etc.) requires:
- Modifying level parser
- Adding new collision logic in MovementResolver
- Creating new sprite types
- Updating save/load systems

### Examples of Difficult Extensions
1. **Valve**: Toggle-able wall that can be opened/closed
2. **Pump**: Speeds up or slows down water flow
3. **Splitter**: Divides one water stream into multiple
4. **Teleporter**: Moves water instantly between two points

### Suggested Solution
Create an entity component system or plugin architecture:
- Base `Entity` class with standard interface
- `EntityRegistry` for dynamic type registration
- Entities define their own collision and rendering behavior

---

## Issue 8: ASCII-Only Level Format

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

## Issue 9: Global Simulation Engine Instance

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

## Issue 10: Emitter ID Assignment Assumes Sequential IDs

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

## Summary Table

| Issue | Severity | Type | Effort |
|-------|----------|------|--------|
| #1 MovementResolver God Object | High | Ext/Maint | High |
| #2 No Config System | Medium | Ext/Usability | Medium |
| #3 Duplicate Direction Maps | Low | Ext/Maint | Low |
| #4 Global Sprite Caches | Medium | Scale/Test | Medium |
| #5 prev_owner Rebuilt Each Tick | Low | Scale/Perf | Low |
| #6 No Spatial Indexing | Medium | Scale | High |
| #7 Hardcoded Entity Types | High | Ext | High |
| #8 ASCII-Only Level Format | Medium | Ext | Medium |
| #9 Global Engine Instance | Low | Test/Ext | Low |
| #10 Sequential Emitter IDs | Low | Ext/Robust | Low |

---

## Recommended Priority

1. **High Priority** (address for major new features):
   - Issue #1: Split MovementResolver
   - Issue #7: Entity type system

2. **Medium Priority** (address for better developer experience):
   - Issue #2: Configuration system
   - Issue #4: Sprite cache management
   - Issue #8: Level format

3. **Low Priority** (address as needed):
   - Issue #3: Direction consolidation
   - Issue #5: prev_owner optimization
   - Issue #6: Spatial indexing (only if large grids needed)
   - Issue #9: Engine injection
   - Issue #10: ID management
