import argparse
import math
import pygame
from dataclasses import dataclass

TILE = 24
FPS = 60
STEP_MS = 120

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

LEVEL_DENSE = [
    "############################",
    "#>...............#........S#",
    "#>........................S#",
    "############################",
]

LEVEL_DENSE = [
    "############################",
    "#>........................S#",
    "#.........................S#",
    "#.........................S#",
    "#.........................S#",
    "#.........................S#",
    "#.........^...............S#",
    "############################",
]

# LEVEL_DENSE = [
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

LEVEL = LEVEL_DENSE

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

def in_bounds(x, y, w, h):
    return 0 <= x < w and 0 <= y < h

def tick(w, h, walls, emitters, sinks, water):
    occupied = set(water.keys())

    for e in emitters:
        tx, ty = e.x + e.dx, e.y + e.dy
        if in_bounds(tx, ty, w, h) and (tx, ty) not in walls and (tx, ty) not in occupied:
            if (tx, ty) in sinks:
                continue
            water[(tx, ty)] = (e.dx, e.dy)
            occupied.add((tx, ty))

    proposals = {}
    for (x, y), (dx, dy) in list(water.items()):
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
                odx, ody = water.get(src, (ndx, ndy))
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
    for (x, y), (dx, dy) in water.items():
        if (x, y) in edges and move_succeeds((x, y)):
            (nx, ny), ndx, ndy = edges[(x, y)]
            if (nx, ny) not in sinks:
                next_water[(nx, ny)] = (ndx, ndy)
        else:
            next_water[(x, y)] = (dx, dy)

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
    for (x, y), (dx, dy) in water.items():
        if grid[y][x] in "#S":
            continue
        grid[y][x] = DIR_TO_CHAR.get((dx, dy), "~")
    return "\n".join("".join(row) for row in grid)

def run_headless(duration_ms, level):
    w, h, walls, emitters, sinks = parse_level(level)
    water = {}
    steps = max(1, int(math.ceil(duration_ms / float(STEP_MS))))
    for _ in range(steps):
        tick(w, h, walls, emitters, sinks, water)
    print(f"Simulated {steps} steps (~{duration_ms} ms)")
    print(render_ascii(w, h, walls, emitters, sinks, water))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without a window for a duration and print ASCII board state.",
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=5000,
        help="Duration to simulate in headless mode.",
    )
    args = parser.parse_args()

    if args.headless:
        run_headless(args.duration_ms, LEVEL)
        return

    pygame.init()
    w, h, walls, emitters, sinks = parse_level(LEVEL)
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

        for (x, y), (dx, dy) in water.items():
            cx, cy = x * TILE + TILE // 2, y * TILE + TILE // 2
            ex, ey = cx + dx * (TILE // 2 - 3), cy + dy * (TILE // 2 - 3)
            pygame.draw.circle(screen, (60, 140, 220), (cx, cy), TILE // 3)
            pygame.draw.line(screen, (200, 230, 255), (cx, cy), (ex, ey), 3)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
