import math

from levels import get_level, parse_level
from simulation import STEP_MS, in_bounds, render_ascii, tick


def run_script(script_text, default_level_name="turn"):
    level_lines = get_level(default_level_name)
    w, h, walls, emitters, sinks = parse_level(level_lines)
    water = {}

    def advance_steps(steps):
        for _ in range(max(0, steps)):
            tick(w, h, walls, emitters, sinks, water)

    def parse_coord(token):
        if "," in token:
            xs, ys = token.split(",", 1)
        elif "x" in token:
            xs, ys = token.split("x", 1)
        else:
            raise ValueError(f"Expected coordinate like '3,4', got '{token}'")
        return int(xs), int(ys)

    for raw in script_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        commands = [cmd.strip() for cmd in line.split(";") if cmd.strip()]
        for cmd in commands:
            parts = cmd.split()
            name = parts[0].lower()
            args = parts[1:]

            if name == "level":
                if not args:
                    raise ValueError("level <name> expected")
                level_lines = get_level(args[0])
                w, h, walls, emitters, sinks = parse_level(level_lines)
                water.clear()
            elif name in ("wait", "step", "steps", "tick"):
                steps = int(args[0]) if args else 1
                advance_steps(steps)
            elif name in ("wait_ms", "sleep"):
                if not args:
                    raise ValueError("wait_ms <millis> expected")
                ms = int(args[0])
                steps = max(1, int(math.ceil(ms / float(STEP_MS))))
                advance_steps(steps)
            elif name in ("add", "wall+", "wall"):
                if not args:
                    raise ValueError("add <x,y>")
                x, y = parse_coord(args[0])
                if not in_bounds(x, y, w, h):
                    continue
                if (x, y) in [(e.x, e.y) for e in emitters]:
                    continue
                if (x, y) in sinks:
                    continue
                walls.add((x, y))
                water.pop((x, y), None)
            elif name in ("remove", "rm", "del", "wall-"):
                if not args:
                    raise ValueError("remove <x,y>")
                x, y = parse_coord(args[0])
                if not in_bounds(x, y, w, h):
                    continue
                walls.discard((x, y))
                water.pop((x, y), None)
            else:
                raise ValueError(f"Unknown script command '{name}'")

    print("Script complete")
    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))
