import argparse
import math
import pygame
from dataclasses import dataclass

TILE = 24
FPS = 60
STEP_MS = 120
STATIONARY_DECAY_MS = 250

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
    "#S.........................#",
    "#..........................#",
    "#.........^................#",
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

_WALL_SURFACE = None
_SINK_SURFACE = None
_EMITTER_SURFACE_CACHE = {}
_WATER_SURFACE_CACHE = {}

@dataclass(frozen=True)
class Emitter:
    id: int
    x: int
    y: int
    dx: int
    dy: int


def _make_surface(color):
    surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    surface.fill(color)
    return surface


def get_wall_surface():
    global _WALL_SURFACE
    if _WALL_SURFACE is None:
        _WALL_SURFACE = _make_surface((80, 80, 80))
    return _WALL_SURFACE


def get_sink_surface():
    global _SINK_SURFACE
    if _SINK_SURFACE is None:
        surface = _make_surface((70, 30, 30))
        center = (TILE // 2, TILE // 2)
        pygame.draw.circle(surface, (20, 10, 10), center, TILE // 4)
        _SINK_SURFACE = surface
    return _SINK_SURFACE


def get_emitter_surface(dx, dy):
    key = (dx, dy)
    if key not in _EMITTER_SURFACE_CACHE:
        surface = _make_surface((160, 140, 40))
        center = (TILE // 2, TILE // 2)
        arrow_end = (
            center[0] + dx * (TILE // 3),
            center[1] + dy * (TILE // 3),
        )
        pygame.draw.line(surface, (30, 20, 10), center, arrow_end, 3)
        _EMITTER_SURFACE_CACHE[key] = surface
    return _EMITTER_SURFACE_CACHE[key]


def get_water_surface(dx, dy):
    key = (dx, dy)
    if key not in _WATER_SURFACE_CACHE:
        surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        center = (TILE // 2, TILE // 2)
        pygame.draw.circle(surface, (60, 140, 220), center, TILE // 3)
        arrow_end = (
            center[0] + dx * (TILE // 2 - 3),
            center[1] + dy * (TILE // 2 - 3),
        )
        pygame.draw.line(surface, (200, 230, 255), center, arrow_end, 3)
        _WATER_SURFACE_CACHE[key] = surface
    return _WATER_SURFACE_CACHE[key]


class TileSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.grid_pos = (x, y)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * TILE, y * TILE)


class WallSprite(TileSprite):
    def __init__(self, x, y):
        super().__init__(x, y, get_wall_surface())


class SinkSprite(TileSprite):
    def __init__(self, x, y):
        super().__init__(x, y, get_sink_surface())


class EmitterSprite(TileSprite):
    def __init__(self, emitter):
        super().__init__(emitter.x, emitter.y, get_emitter_surface(emitter.dx, emitter.dy))


class WaterSprite(TileSprite):
    def __init__(self, x, y, dx, dy):
        super().__init__(x, y, get_water_surface(dx, dy))
        self.dx = dx
        self.dy = dy

    def update_state(self, x, y, dx, dy):
        if (dx, dy) != (self.dx, self.dy):
            self.image = get_water_surface(dx, dy)
        self.dx, self.dy = dx, dy
        if (x, y) != self.grid_pos:
            self.grid_pos = (x, y)
            self.rect.topleft = (x * TILE, y * TILE)


def build_static_sprites(walls, sinks, emitters):
    static_sprites = pygame.sprite.Group()
    wall_lookup = {}
    for (x, y) in walls:
        sprite = WallSprite(x, y)
        wall_lookup[(x, y)] = sprite
        static_sprites.add(sprite)
    for (x, y) in sinks:
        static_sprites.add(SinkSprite(x, y))
    for emitter in emitters:
        static_sprites.add(EmitterSprite(emitter))
    return static_sprites, wall_lookup


def sync_water_sprites(water_state, water_group):
    existing = {(sprite.grid_pos): sprite for sprite in water_group.sprites()}
    missing = set(existing.keys()) - set(water_state.keys())
    for pos in missing:
        existing[pos].kill()
        existing.pop(pos, None)

    for (x, y), (dx, dy, _age, _eid) in water_state.items():
        sprite = existing.get((x, y))
        if sprite is None:
            water_group.add(WaterSprite(x, y, dx, dy))
        else:
            sprite.update_state(x, y, dx, dy)

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
                emitters.append(Emitter(len(emitters), x, y, dx, dy))
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
    emitter_positions = {(e.x, e.y) for e in emitters}

    for e in emitters:
        tx, ty = e.x + e.dx, e.y + e.dy
        if in_bounds(tx, ty, w, h) and (tx, ty) not in walls and (tx, ty) not in occupied and (tx, ty) not in emitter_positions:
            if (tx, ty) in sinks:
                continue
            water[(tx, ty)] = (e.dx, e.dy, 0, e.id)
            occupied.add((tx, ty))

    proposals = {}
    for (x, y), (dx, dy, age, eid) in list(water.items()):
        fx, fy = x + dx, y + dy
        forward_blocked = (
            not in_bounds(fx, fy, w, h)
            or (fx, fy) in walls
            or (fx, fy) in emitter_positions
        )

        if not forward_blocked:
            proposals[(x, y)] = (fx, fy, dx, dy, eid)
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
            if (nx, ny) in emitter_positions:
                continue
            chosen = (nx, ny, ndx, ndy, eid)
            break
        if chosen is None:
            proposals[(x, y)] = (x, y, dx, dy, eid)
        else:
            proposals[(x, y)] = chosen

    targets = {}
    for src, (nx, ny, ndx, ndy, eid) in proposals.items():
        targets.setdefault((nx, ny), []).append((src, ndx, ndy, eid))

    inflow_targets = {}
    for tgt, movers in targets.items():
        incoming_ids = {eid for (src, _, _, eid) in movers if src != tgt}
        if incoming_ids:
            inflow_targets[tgt] = incoming_ids

    edges = {}
    for tgt, movers in targets.items():
        if tgt in sinks:
            for (src, ndx, ndy, eid) in movers:
                edges[src] = (tgt, ndx, ndy, eid)
            continue
        if len(movers) == 1:
            (src, ndx, ndy, eid) = movers[0]
            edges[src] = (tgt, ndx, ndy, eid)
        else:
            def priority(move):
                src, ndx, ndy, eid = move
                odx, ody, _, _ = water.get(src, (ndx, ndy, 0, eid))
                straight = (ndx, ndy) == (odx, ody)
                return (0 if straight else 1, src[1], src[0])
            src, ndx, ndy, eid = min(movers, key=priority)
            edges[src] = (tgt, ndx, ndy, eid)

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
        tgt, _, _, _ = edges[src]
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
    for (x, y), (dx, dy, age, eid) in water.items():
        if (x, y) in edges and move_succeeds((x, y)):
            (nx, ny), ndx, ndy, neid = edges[(x, y)]
            if (nx, ny) not in sinks:
                moved = (nx, ny) != (x, y)
                if moved:
                    new_age = 0
                else:
                    inflow_ids = inflow_targets.get((nx, ny), set())
                    new_age = 0 if neid in inflow_ids else age + 1
                if new_age < decay_steps:
                    next_water[(nx, ny)] = (ndx, ndy, new_age, neid)
        else:
            inflow_ids = inflow_targets.get((x, y), set())
            new_age = 0 if eid in inflow_ids else age + 1
            if new_age < decay_steps:
                next_water[(x, y)] = (dx, dy, new_age, eid)

    water.clear()
    water.update(next_water)

def render_ascii(w, h, walls, emitters, sinks, water, show_coords=False):
    grid = [["." for _ in range(w)] for _ in range(h)]
    for (x, y) in walls:
        grid[y][x] = "#"
    for (x, y) in sinks:
        grid[y][x] = "S"
    for e in emitters:
        grid[e.y][e.x] = DIR_TO_CHAR.get((e.dx, e.dy), "E")
    for (x, y), (dx, dy, age, _eid) in water.items():
        if grid[y][x] in "#S":
            continue
        grid[y][x] = DIR_TO_CHAR.get((dx, dy), "~")
    if not show_coords:
        return "\n".join("".join(row) for row in grid)

    label_w = max(2, len(str(h - 1)))
    header = " " * (label_w + 1) + "".join(str(x % 10) for x in range(w))
    lines = [header]
    for y, row in enumerate(grid):
        lines.append(f"{y:>{label_w}} " + "".join(row))
    return "\n".join(lines)

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
    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))

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
    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))

def main():
    def draw_coords(surface, w, h, font):
        color = (140, 140, 140)
        for x in range(w):
            label = font.render(str(x % 10), True, color)
            surface.blit(label, (x * TILE + 4, 2))
        for y in range(h):
            label = font.render(str(y), True, color)
            surface.blit(label, (2, y * TILE + 2))

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
    font = pygame.font.SysFont(None, 14)
    clock = pygame.time.Clock()
    emitter_positions = {(e.x, e.y) for e in emitters}
    static_sprites, wall_lookup = build_static_sprites(walls, sinks, emitters)
    water_sprites = pygame.sprite.Group()

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
                    water_sprites.empty()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                gx, gy = mx // TILE, my // TILE
                if (gx, gy) not in emitter_positions:
                    if event.button == 1:
                        if (gx, gy) in walls:
                            walls.remove((gx, gy))
                            sprite = wall_lookup.pop((gx, gy), None)
                            if sprite:
                                sprite.kill()
                        else:
                            walls.add((gx, gy))
                            sprite = WallSprite(gx, gy)
                            wall_lookup[(gx, gy)] = sprite
                            static_sprites.add(sprite)
                    elif event.button == 3:
                        water.pop((gx, gy), None)

        if not paused:
            while step_acc >= STEP_MS:
                step_acc -= STEP_MS
                tick(w, h, walls, emitters, sinks, water)

        sync_water_sprites(water, water_sprites)
        screen.fill((20, 20, 20))
        static_sprites.draw(screen)
        water_sprites.draw(screen)
        draw_coords(screen, w, h, font)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
