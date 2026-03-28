---
title: Hardcoded Entity Type System
labels: priority: high, type: extensibility
---

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

*This issue was automatically generated from the scalability and extensibility analysis in PR #1.*
