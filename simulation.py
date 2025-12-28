import math
from typing import Mapping, Set

from ascii_renderer import AsciiRenderer
from levels import parse_level
from movement_resolver import in_bounds
from simulation_constants import STATIONARY_DECAY_MS, STEP_MS, WATER_DIR_CHAR
from simulation_engine import SimulationEngine
from simulation_state import SimulationState, WaterCell, clear_sink_claims
from typedefs import Coord


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
