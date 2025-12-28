import math
from typing import Callable, Dict, Iterable, List

from levels import get_level, parse_level
from simulation import STEP_MS, SimulationState, clear_sink_claims, in_bounds, render_ascii, tick
from typedefs import Coord


def run_script(script_text: str, default_level_name: str = "turn") -> None:
    state = SimulationState()
    clear_sink_claims(state)
    level_lines = get_level(default_level_name)
    w, h, walls, emitters, sinks = parse_level(level_lines)
    emitter_positions = {(e.x, e.y) for e in emitters}
    water = state.water

    def advance_steps(steps: int) -> None:
        for _ in range(max(0, steps)):
            tick(w, h, walls, emitters, sinks, state)

    def parse_coord(token: str) -> Coord:
        if "," in token:
            xs, ys = token.split(",", 1)
        elif "x" in token:
            xs, ys = token.split("x", 1)
        else:
            raise ValueError(f"Expected coordinate like '3,4', got '{token}'")
        return int(xs), int(ys)

    def handle_level(args: List[str]) -> None:
        nonlocal w, h, walls, emitters, sinks, level_lines
        if not args:
            raise ValueError("level <name> expected")
        level_lines = get_level(args[0])
        w, h, walls, emitters, sinks = parse_level(level_lines)
        emitter_positions.clear()
        emitter_positions.update((e.x, e.y) for e in emitters)
        state.clear_water()

    def handle_wait(args: List[str]) -> None:
        steps = int(args[0]) if args else 1
        advance_steps(steps)

    def handle_wait_ms(args: List[str]) -> None:
        if not args:
            raise ValueError("wait_ms <millis> expected")
        ms = int(args[0])
        steps = max(1, int(math.ceil(ms / float(STEP_MS))))
        advance_steps(steps)

    def handle_add(args: List[str]) -> None:
        if not args:
            raise ValueError("add <x,y>")
        x, y = parse_coord(args[0])
        if not in_bounds(x, y, w, h):
            return
        if (x, y) in emitter_positions or (x, y) in sinks:
            return
        walls.add((x, y))
        water.pop((x, y), None)

    def handle_remove(args: List[str]) -> None:
        if not args:
            raise ValueError("remove <x,y>")
        x, y = parse_coord(args[0])
        if not in_bounds(x, y, w, h):
            return
        walls.discard((x, y))
        water.pop((x, y), None)

    def build_handlers() -> Dict[str, Callable[[List[str]], None]]:
        handlers: Dict[str, Callable[[List[str]], None]] = {}

        def register(names: Iterable[str], func: Callable[[List[str]], None]) -> None:
            for name in names:
                handlers[name] = func

        register(("level",), handle_level)
        register(("wait", "step", "steps", "tick"), handle_wait)
        register(("wait_ms", "sleep"), handle_wait_ms)
        register(("add", "wall+", "wall"), handle_add)
        register(("remove", "rm", "del", "wall-"), handle_remove)
        return handlers

    handlers = build_handlers()

    for raw in script_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        commands = [cmd.strip() for cmd in line.split(";") if cmd.strip()]
        for cmd in commands:
            parts = cmd.split()
            name = parts[0].lower()
            args = parts[1:]

            handler = handlers.get(name)
            if handler is None:
                raise ValueError(f"Unknown script command '{name}'")
            handler(args)

    print("Script complete")
    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))
