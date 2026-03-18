"""
BFS solver for the flow game.

Finds the minimum set of wall placements that routes all water to sinks.
Computationally isolated from the UI — no pygame imports.
"""

from collections import deque
from typing import FrozenSet, List, Optional

from simulation_engine import SimulationEngine
from simulation_state import SimulationState
from typedefs import Coord

_SOLVE_STEPS = 200


def _is_solved(engine, w, h, all_walls, emitters, sinks) -> bool:
    if not sinks:
        return False
    state = SimulationState()
    for _ in range(_SOLVE_STEPS):
        engine.tick(w, h, all_walls, emitters, sinks, state)
    return all(sink in state.sink_claims for sink in sinks)


def _get_water_cells(engine, w, h, all_walls, emitters, sinks, steps=50):
    state = SimulationState()
    for _ in range(steps):
        engine.tick(w, h, all_walls, emitters, sinks, state)
    return set(state.water.keys())


def _candidate_walls(water_cells, all_walls, emitter_positions, sinks, w, h):
    """Open cells adjacent to water flow — best candidates for wall placement."""
    candidates = set()
    for (x, y) in water_cells:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < w
                and 0 <= ny < h
                and (nx, ny) not in all_walls
                and (nx, ny) not in emitter_positions
                and (nx, ny) not in sinks
                and (nx, ny) not in water_cells
            ):
                candidates.add((nx, ny))
    return candidates


def solve(
    w: int,
    h: int,
    fixed_walls: FrozenSet[Coord],
    emitters,
    sinks,
    player_walls: FrozenSet[Coord] = frozenset(),
    max_extra_walls: int = 6,
) -> Optional[List[Coord]]:
    """
    BFS to find the minimum additional wall placements needed to win.

    Returns the ordered list of walls to add, or None if no solution is found
    within max_extra_walls.
    """
    engine = SimulationEngine()
    emitter_positions = frozenset((e.x, e.y) for e in emitters)
    fixed = frozenset(fixed_walls)

    if _is_solved(engine, w, h, fixed | player_walls, emitters, sinks):
        return []

    queue = deque([(player_walls, [])])
    visited = {player_walls}

    while queue:
        walls, path = queue.popleft()
        if len(path) >= max_extra_walls:
            continue

        all_walls = fixed | walls
        water_cells = _get_water_cells(engine, w, h, all_walls, emitters, sinks)
        if not water_cells:
            continue

        candidates = _candidate_walls(water_cells, all_walls, emitter_positions, sinks, w, h)

        for cell in sorted(candidates):
            new_walls = walls | frozenset([cell])
            if new_walls in visited:
                continue
            visited.add(new_walls)
            new_all_walls = fixed | new_walls
            new_path = path + [cell]
            if _is_solved(engine, w, h, new_all_walls, emitters, sinks):
                return new_path
            queue.append((new_walls, new_path))

    return None


def get_hint(
    w: int,
    h: int,
    fixed_walls: FrozenSet[Coord],
    emitters,
    sinks,
    player_walls: FrozenSet[Coord] = frozenset(),
) -> Optional[Coord]:
    """Return the first wall to place as a hint, or None if already solved or unsolvable."""
    solution = solve(w, h, fixed_walls, emitters, sinks, player_walls)
    if solution:
        return solution[0]
    return None
