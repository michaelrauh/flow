import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Set, Tuple

from levels import DIR_TO_CHAR, SINK, parse_level
from typedefs import Coord

STEP_MS = 120
STATIONARY_DECAY_MS = 250
WATER_DIR_CHAR = {
    (0, -1): "U",
    (1, 0): "R",
    (0, 1): "D",
    (-1, 0): "L",
}


@dataclass
class WaterCell:
    dx: int
    dy: int
    age: int
    emitter_id: int
    prefer_left: bool


@dataclass
class SimulationState:
    water: Dict[Coord, WaterCell] = field(default_factory=dict)
    sink_claims: Dict[Coord, int] = field(default_factory=dict)

    def clear_water(self) -> None:
        self.water.clear()

    def clear_sink_claims(self) -> None:
        self.sink_claims.clear()


def clear_sink_claims(state: SimulationState) -> None:
    state.clear_sink_claims()


def in_bounds(x: int, y: int, w: int, h: int) -> bool:
    return 0 <= x < w and 0 <= y < h


class MovementResolver:
    def __init__(self, w: int, h: int, walls: Set[Coord], emitters, sinks: Set[Coord], state: SimulationState):
        self.w = w
        self.h = h
        self.walls = walls
        self.emitters = list(emitters)
        self.sinks = sinks
        self.state = state
        self.emitter_positions = {(e.x, e.y) for e in self.emitters}
        self.prev_owner = {pos: cell.emitter_id for pos, cell in state.water.items()}

    def spawn_from_emitters(self, occupied: Set[Coord]) -> None:
        for emitter in self.emitters:
            tx, ty = emitter.x + emitter.dx, emitter.y + emitter.dy
            if not in_bounds(tx, ty, self.w, self.h):
                continue
            if (tx, ty) in self.walls or (tx, ty) in occupied or (tx, ty) in self.emitter_positions:
                continue
            if (tx, ty) in self.sinks:
                continue
            self.state.water[(tx, ty)] = WaterCell(emitter.dx, emitter.dy, 0, emitter.id, True)
            occupied.add((tx, ty))

    def _propose_move(self, position: Coord, cell: WaterCell):
        x, y = position
        fx, fy = x + cell.dx, y + cell.dy
        forward_blocked = (
            not in_bounds(fx, fy, self.w, self.h)
            or (fx, fy) in self.walls
            or (fx, fy) in self.emitter_positions
        )

        if (fx, fy) in self.sinks:
            owner = self.state.sink_claims.get((fx, fy))
            if owner is not None and owner != cell.emitter_id:
                forward_blocked = True

        if not forward_blocked:
            return position, (fx, fy, cell.dx, cell.dy, cell.emitter_id, cell.prefer_left)

        ldx, ldy = cell.dy, -cell.dx
        rdx, rdy = -cell.dy, cell.dx
        turn_order = ((ldx, ldy), (rdx, rdy)) if cell.prefer_left else ((rdx, rdy), (ldx, ldy))
        for ndx, ndy in turn_order:
            nx, ny = x + ndx, y + ndy
            if not in_bounds(nx, ny, self.w, self.h):
                continue
            if (nx, ny) in self.walls or (nx, ny) in self.emitter_positions:
                continue
            if (nx, ny) in self.sinks:
                owner = self.state.sink_claims.get((nx, ny))
                if owner is not None and owner != cell.emitter_id:
                    continue
            return position, (nx, ny, ndx, ndy, cell.emitter_id, not cell.prefer_left)

        return position, (x, y, cell.dx, cell.dy, cell.emitter_id, cell.prefer_left)

    def build_proposals(self) -> Dict[Coord, Tuple[int, int, int, int, int, bool]]:
        proposals: Dict[Coord, Tuple[int, int, int, int, int, bool]] = {}
        for position, cell in list(self.state.water.items()):
            src, proposal = self._propose_move(position, cell)
            proposals[src] = proposal
        return proposals

    @staticmethod
    def group_targets(proposals: Mapping[Coord, Tuple[int, int, int, int, int, bool]]) -> Dict[Coord, List[Tuple[Coord, int, int, int, bool]]]:
        targets: Dict[Coord, List[Tuple[Coord, int, int, int, bool]]] = {}
        for src, (nx, ny, ndx, ndy, eid, pref_left) in proposals.items():
            targets.setdefault((nx, ny), []).append((src, ndx, ndy, eid, pref_left))
        return targets

    @staticmethod
    def build_inflow_targets(targets: Mapping[Coord, Iterable[Tuple[Coord, int, int, int, bool]]]) -> Dict[Coord, Set[int]]:
        inflow_targets: Dict[Coord, Set[int]] = {}
        for tgt, movers in targets.items():
            incoming_ids = {eid for (src, _ndx, _ndy, eid, _pref) in movers if src != tgt}
            if incoming_ids:
                inflow_targets[tgt] = incoming_ids
        return inflow_targets

    def _select_edges(self, targets: Mapping[Coord, List[Tuple[Coord, int, int, int, bool]]]) -> Dict[Coord, Tuple[Coord, int, int, int, bool]]:
        edges: Dict[Coord, Tuple[Coord, int, int, int, bool]] = {}
        for tgt, movers in targets.items():
            if tgt in self.sinks:
                if len(movers) == 1:
                    src, ndx, ndy, eid, pref_left = movers[0]
                else:
                    src, ndx, ndy, eid, pref_left = min(
                        movers,
                        key=lambda m: (
                            0 if self.state.sink_claims.get(tgt) == m[3] else 1,
                            m[0][1],
                            m[0][0],
                        ),
                    )
                self.state.sink_claims[tgt] = eid
                edges[src] = (tgt, ndx, ndy, eid, pref_left)
                continue

            if len(movers) == 1:
                src, ndx, ndy, eid, pref_left = movers[0]
                edges[src] = (tgt, ndx, ndy, eid, pref_left)
                continue

            def priority(move: Tuple[Coord, int, int, int, bool]) -> Tuple[int, int, int, int]:
                src, ndx, ndy, eid, pref_left = move
                cell = self.state.water.get(src, WaterCell(ndx, ndy, 0, eid, pref_left))
                straight = (ndx, ndy) == (cell.dx, cell.dy)
                owner_bonus = 0 if self.prev_owner.get(tgt) == eid else 1
                return (owner_bonus, 0 if straight else 1, src[1], src[0])

            src, ndx, ndy, eid, pref_left = min(movers, key=priority)
            edges[src] = (tgt, ndx, ndy, eid, pref_left)
        return edges

    def _move_succeeds(
        self,
        src: Coord,
        edges: Mapping[Coord, Tuple[Coord, int, int, int, bool]],
        occupied_now: Set[Coord],
        memo: Dict[Coord, bool],
        visiting: Set[Coord],
    ) -> bool:
        if src in memo:
            return memo[src]
        if src not in edges:
            memo[src] = False
            return False
        tgt, _ndx, _ndy, _eid, _pref = edges[src]
        if tgt in self.sinks:
            memo[src] = True
            return True
        if tgt not in occupied_now:
            memo[src] = True
            return True
        if tgt == src:
            memo[src] = True
            return True
        if tgt in visiting:
            memo[src] = True
            return True
        visiting.add(tgt)
        memo[src] = self._move_succeeds(tgt, edges, occupied_now, memo, visiting)
        visiting.remove(tgt)
        return memo[src]

    def advance_water(
        self,
        edges: Mapping[Coord, Tuple[Coord, int, int, int, bool]],
        inflow_targets: Mapping[Coord, Set[int]],
        decay_steps: int,
    ) -> Dict[Coord, WaterCell]:
        next_water: Dict[Coord, WaterCell] = {}
        memo: Dict[Coord, bool] = {}
        visiting: Set[Coord] = set()
        occupied_now = set(self.state.water.keys())

        for (x, y), cell in self.state.water.items():
            if (x, y) in edges and self._move_succeeds((x, y), edges, occupied_now, memo, visiting):
                (nx, ny), ndx, ndy, neid, npref = edges[(x, y)]
                if (nx, ny) not in self.sinks:
                    moved = (nx, ny) != (x, y)
                    if moved:
                        new_age = 0
                    else:
                        inflow_ids = inflow_targets.get((nx, ny), set())
                        new_age = 0 if neid in inflow_ids else cell.age + 1
                    if new_age < decay_steps:
                        next_water[(nx, ny)] = WaterCell(ndx, ndy, new_age, neid, npref)
            else:
                inflow_ids = inflow_targets.get((x, y), set())
                new_age = 0 if cell.emitter_id in inflow_ids else cell.age + 1
                if new_age < decay_steps:
                    next_water[(x, y)] = WaterCell(cell.dx, cell.dy, new_age, cell.emitter_id, cell.prefer_left)

        return next_water


class WaterPruner:
    @staticmethod
    def prune(next_water: Mapping[Coord, WaterCell], emitters: Iterable) -> Dict[Coord, WaterCell]:
        positions_by_eid: Dict[int, Set[Coord]] = {}
        for position, cell in next_water.items():
            positions_by_eid.setdefault(cell.emitter_id, set()).add(position)

        reachable: Dict[int, Set[Coord]] = {}
        for emitter in emitters:
            seen = reachable.setdefault(emitter.id, set())
            positions = list(positions_by_eid.get(emitter.id, set()))
            if not positions:
                continue
            min_dist = min(abs(nx - emitter.x) + abs(ny - emitter.y) for (nx, ny) in positions)
            seeds = [(nx, ny) for (nx, ny) in positions if abs(nx - emitter.x) + abs(ny - emitter.y) == min_dist]
            stack = list(seeds)
            while stack:
                pos = stack.pop()
                if pos in seen:
                    continue
                seen.add(pos)
                x, y = pos
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (nx, ny) in positions_by_eid.get(emitter.id, set()):
                        stack.append((nx, ny))

        filtered: Dict[Coord, WaterCell] = {}
        for position, cell in next_water.items():
            if position in reachable.get(cell.emitter_id, set()):
                filtered[position] = cell
        return filtered


class SimulationEngine:
    def __init__(self, step_ms: int = STEP_MS, decay_ms: int = STATIONARY_DECAY_MS):
        self.step_ms = step_ms
        self.decay_ms = decay_ms

    @property
    def decay_steps(self) -> int:
        return max(1, int(math.ceil(self.decay_ms / float(self.step_ms))))

    def tick(
        self,
        w: int,
        h: int,
        walls: Set[Coord],
        emitters,
        sinks: Set[Coord],
        state: SimulationState,
    ) -> None:
        if not state.water:
            state.clear_sink_claims()

        occupied = set(state.water.keys())
        resolver = MovementResolver(w, h, walls, emitters, sinks, state)
        resolver.spawn_from_emitters(occupied)

        proposals = resolver.build_proposals()
        targets = resolver.group_targets(proposals)
        inflow_targets = resolver.build_inflow_targets(targets)
        edges = resolver._select_edges(targets)

        next_water = resolver.advance_water(edges, inflow_targets, self.decay_steps)
        filtered = WaterPruner.prune(next_water, emitters)

        state.clear_water()
        state.water.update(filtered)


_ENGINE = SimulationEngine()


def tick(
    w: int,
    h: int,
    walls: Set[Coord],
    emitters,
    sinks: Set[Coord],
    state: SimulationState,
) -> None:
    _ENGINE.tick(w, h, walls, emitters, sinks, state)


class AsciiRenderer:
    @staticmethod
    def render(
        w: int,
        h: int,
        walls,
        emitters,
        sinks,
        water: Mapping[Coord, WaterCell],
        show_coords: bool = False,
    ) -> str:
        grid = [["." for _ in range(w)] for _ in range(h)]
        for (x, y) in walls:
            grid[y][x] = "#"
        for (x, y) in sinks:
            grid[y][x] = SINK
        for e in emitters:
            grid[e.y][e.x] = DIR_TO_CHAR.get((e.dx, e.dy), "E")
        for (x, y), cell in water.items():
            dx, dy = cell.dx, cell.dy
            if grid[y][x] in f"#{SINK}":
                continue
            grid[y][x] = WATER_DIR_CHAR.get((dx, dy), "~")
        if not show_coords:
            return "\n".join("".join(row) for row in grid)

        label_w = max(2, len(str(h - 1)))
        header = " " * (label_w + 1) + "".join(str(x % 10) for x in range(w))
        lines = [header]
        for y, row in enumerate(grid):
            lines.append(f"{y:>{label_w}} " + "".join(row))
        return "\n".join(lines)


def render_ascii(
    w: int,
    h: int,
    walls,
    emitters,
    sinks,
    water: Mapping[Coord, WaterCell],
    show_coords: bool = False,
) -> str:
    return AsciiRenderer.render(w, h, walls, emitters, sinks, water, show_coords)


def run_headless(duration_ms, level_lines) -> None:
    state = SimulationState()
    w, h, walls, emitters, sinks = parse_level(level_lines)
    steps = max(1, int(math.ceil(duration_ms / float(STEP_MS))))
    for _ in range(steps):
        tick(w, h, walls, emitters, sinks, state)
    print(f"Simulated {steps} steps (~{duration_ms} ms)")
    print(render_ascii(w, h, walls, emitters, sinks, state.water, show_coords=True))
