import math
from typing import Set

from movement_resolver import MovementResolver
from simulation_constants import STATIONARY_DECAY_MS, STEP_MS
from simulation_state import SimulationState
from water_pruner import WaterPruner


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
        walls,
        emitters,
        sinks: Set,
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
