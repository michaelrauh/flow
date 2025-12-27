import argparse
import math
import pygame
from dataclasses import dataclass

TILE = 24
FPS = 60
STEP_MS = 120
STATIONARY_DECAY_MS = 5000

LEVEL_BACKUP = [
    "####################",
    "#..>...............#",
    "#..####..#####..#..#",
    "#.......#.....#..#..#",
    "#..#....#..#..#..#..#",
    "#..#....#..#..#..#..#",
    "#..#...............<#",
    "####################",
]

LEVEL_DENSE_WIDE = [
    "############################",
    "#>...............#........S#",
    "#>........................S#",
    "############################",
]

LEVEL_DENSE_TURN = [
    "############################",
    "#>........................S#",
    "#..........................#",
    "#..........................#",
    "#..........................#",
    "#..........................#",
    "#.........^...............S#",
    "############################",
]

# LEVEL_MAZE = [
#     "############################",
#     "#>..#....#....#....#....#..#",
#     "#.#.#.##.#.##.#.##.#.##.#..#",
#     "#.#...#..#....#..#...#..#..#",
#     "#.###.#.####.#.###.#.##.#..#",
#     "#....#.#....#.#...#....#.#.#",
#     "####.#.####.#.#.#####.##.#.#",
#     "#....#...#.#.#....#....#...#",
#     "#.#####.#.#.###.#.###.#.#..#",
#     "#..#...#.#.#...#.#...#....<#",
#     "#..#.##.#.#.###.#.##.#.##..#",
#     "############################",
# ]

LEVEL = LEVEL_DENSE_TURN
LEVELS = {
    "backup": LEVEL_BACKUP,
    "wide": LEVEL_DENSE_WIDE,
    "turn": LEVEL_DENSE_TURN,
}

DIRS = {
    "^": (0, -1),
    ">": (1, 0),
    "v": (0, 1),
    "<": (-1, 0),
}
DIR_TO_CHAR = {v: k for k, v in DIRS.items()}
SINK = "S"
@dataclass(frozen=True)
class Emitter:
    x: int
    y: int
    dx: int
    dy: int

def parse_level(lines):
    h = len(lines)
    w = max(len(r) for r in lines)
    walls = set()
    emitters = []
    sinks = set()
    for y, row in enumerate(lines):
        for x, ch in enumerate(row):
            if ch == "#":
                walls.add((x, y))
            elif ch in DIRS:
                dx, dy = DIRS[ch]
                emitters.append(Emitter(x, y, dx, dy))
            elif ch == SINK:
                sinks.add((x, y))
    return w, h, walls, emitters, sinks

def get_level(name):
    if name in LEVELS:
        return LEVELS[name]
    raise ValueError(f"Unknown level '{name}'. Known levels: {', '.join(sorted(LEVELS))}")

def in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h

def tick(w, h, walls, emitters, sinks, water):
    decay_steps = max(1, int(math.ceil(STATIONARY_DECAY_MS / float(STEP_MS))))
    occupied = set(water.keys())

    for e in emitters:
        tx, ty = e.x + e.dx, e.y + e.dy
        if in_bounds(tx, ty, w, h) and (tx, ty) not in walls and (tx, ty) not in occupied:
            if (tx, ty) in sinks:
                continue
            water[(tx, ty)] = (e.dx, e.dy, 0)
            occupied.add((tx, ty))

    proposals = {}
    for (x, y), (dx, dy, age) in list(water.items()):
        fx, fy = x + dx, y + dy
        forward_blocked = (
            not in_bounds(fx, fy, w, h)
            or (fx, fy) in walls
        )

        if not forward_blocked:
            proposals[(x, y)] = (fx, fy, dx, dy)
            continue

        ldx, ldy = dy, -dx
        rdx, rdy = -dy, dx
        chosen = None
        for ndx, ndy in ((ldx, ldy), (rdx, rdy)):
            nx, ny = x + ndx, y + ndy
            if not in_bounds(nx, ny, w, h):
                continue
            if (nx, ny) in walls:
                continue
            chosen = (nx, ny, ndx, ndy)
            break
        if chosen is None:
            proposals[(x, y)] = (x, y, dx, dy)
        else:
            proposals[(x, y)] = chosen

    targets = {}
    for src, (nx, ny, ndx, ndy) in proposals.items():
        targets.setdefault((nx, ny), []).append((src, ndx, ndy))

    edges = {}
    for tgt, movers in targets.items():
        if tgt in sinks:
            for (src, ndx, ndy) in movers:
                edges[src] = (tgt, ndx, ndy)
            continue
        if len(movers) == 1:
            (src, ndx, ndy) = movers[0]
            edges[src] = (tgt, ndx, ndy)
        else:
            def priority(move):
                src, ndx, ndy = move
                odx, ody, _ = water.get(src, (ndx, ndy, 0))
                straight = (ndx, ndy) == (odx, ody)
                return (0 if straight else 1, src[1], src[0])
            src, ndx, ndy = min(movers, key=priority)
            edges[src] = (tgt, ndx, ndy)

    memo = {}
    visiting = set()
    occupied_now = set(water.keys())

    def move_succeeds(src):
        # Allow moves into cells being vacated by following chains; cycles rotate successfully.
        if src in memo:
            return memo[src]
        if src not in edges:
            memo[src] = False
            return False
        tgt, _, _ = edges[src]
        if tgt in sinks:
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
        memo[src] = move_succeeds(tgt)
        visiting.remove(tgt)
        return memo[src]

    next_water = {}
    for (x, y), (dx, dy, age) in water.items():
        if (x, y) in edges and move_succeeds((x, y)):
            (nx, ny), ndx, ndy = edges[(x, y)]
            if (nx, ny) not in sinks:
                new_age = 0 if (nx, ny) != (x, y) else age + 1
                if new_age < decay_steps:
                    next_water[(nx, ny)] = (ndx, ndy, new_age)
        else:
            new_age = age + 1
            if new_age < decay_steps:
                next_water[(x, y)] = (dx, dy, new_age)

    water.clear()
    water.update(next_water)

def render_ascii(w, h, walls, emitters, sinks, water):
    grid = [["." for _ in range(w)] for _ in range(h)]
    for (x, y) in walls:
        grid[y][x] = "#"
    for (x, y) in sinks:
        grid[y][x] = "S"
    for e in emitters:
        grid[e.y][e.x] = DIR_TO_CHAR.get((e.dx, e.dy), "E")
    for (x, y), (dx, dy, age) in water.items():
        if grid[y][x] in "#S":
            continue
        grid[y][x] = DIR_TO_CHAR.get((dx, dy), "~")
    return "\n".join("".join(row) for row in grid)

def run_headless(duration_ms, level, script=None, level_name="turn"):
    if script:
        run_script(script, level_name)
        return
    w, h, walls, emitters, sinks = parse_level(level)
    water = {}
    steps = max(1, int(math.ceil(duration_ms / float(STEP_MS))))
    for _ in range(steps):
        tick(w, h, walls, emitters, sinks, water)
    print(f"Simulated {steps} steps (~{duration_ms} ms)")
    print(render_ascii(w, h, walls, emitters, sinks, water))

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
        # Support semicolon-separated commands on one line
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
    print(render_ascii(w, h, walls, emitters, sinks, water))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without a window for a duration and print ASCII board state.",
    )
    parser.add_argument(
        "--level",
        default="turn",
        help="Level to load (choices: {}).".format(", ".join(sorted(LEVELS))),
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=5000,
        help="Duration to simulate in headless mode.",
    )
    parser.add_argument(
        "--script",
        help="Tiny DSL: commands separated by newlines/semicolons: level NAME | wait N | wait_ms MS | add X,Y | remove X,Y",
    )
    parser.add_argument(
        "--script-file",
        help="Path to a script file using the DSL (ignored if --script is provided).",
    )
    args = parser.parse_args()

    level_lines = get_level(args.level)

    script_text = None
    if args.script:
        script_text = args.script
    elif args.script_file:
        with open(args.script_file, "r") as fh:
            script_text = fh.read()

    if args.headless:
        run_headless(args.duration_ms, level_lines, script=script_text, level_name=args.level)
        return

    pygame.init()
    w, h, walls, emitters, sinks = parse_level(level_lines)
    screen = pygame.display.set_mode((w * TILE, h * TILE))
    clock = pygame.time.Clock()

    water = {}
    step_acc = 0
    running = True
    paused = False

    while running:
        dt = clock.tick(FPS)
        step_acc += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n:
                    tick(w, h, walls, emitters, sinks, water)
                elif event.key == pygame.K_r:
                    water.clear()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                gx, gy = mx // TILE, my // TILE
                if (gx, gy) not in [(e.x, e.y) for e in emitters]:
                    if event.button == 1:
                        if (gx, gy) in walls:
                            walls.remove((gx, gy))
                        else:
                            walls.add((gx, gy))
                    elif event.button == 3:
                        water.pop((gx, gy), None)

        if not paused:
            while step_acc >= STEP_MS:
                step_acc -= STEP_MS
                tick(w, h, walls, emitters, sinks, water)

        screen.fill((20, 20, 20))

        for (x, y) in walls:
            pygame.draw.rect(screen, (80, 80, 80), (x * TILE, y * TILE, TILE, TILE))

        for (x, y) in sinks:
            pygame.draw.rect(screen, (70, 30, 30), (x * TILE, y * TILE, TILE, TILE))
            cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
            pygame.draw.circle(screen, (20, 10, 10), (cx, cy), TILE // 4)

        for e in emitters:
            pygame.draw.rect(screen, (160, 140, 40), (e.x * TILE, e.y * TILE, TILE, TILE))
            cx, cy = e.x * TILE + TILE // 2, e.y * TILE + TILE // 2
            ax, ay = cx + e.dx * (TILE // 3), cy + e.dy * (TILE // 3)
            pygame.draw.line(screen, (30, 20, 10), (cx, cy), (ax, ay), 3)

        for (x, y), (dx, dy, age) in water.items():
            cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
            ex, ey = cx + dx * (TILE // 2 - 3), cy + dy * (TILE // 2 - 3)
            pygame.draw.circle(screen, (60, 140, 220), (cx, cy), TILE // 3)
            pygame.draw.line(screen, (200, 230, 255), (cx, cy), (ex, ey), 3)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
