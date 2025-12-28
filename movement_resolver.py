from typing import Dict, Iterable, List, Mapping, MutableMapping, Set, Tuple

from simulation_state import SimulationState, WaterCell
from typedefs import Coord


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
