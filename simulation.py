import math

from levels import DIR_TO_CHAR, SINK, parse_level

STEP_MS = 120
STATIONARY_DECAY_MS = 250
WATER_DIR_CHAR = {
    (0, -1): "U",
    (1, 0): "R",
    (0, 1): "D",
    (-1, 0): "L",
}


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
        grid[y][x] = SINK
    for e in emitters:
        grid[e.y][e.x] = DIR_TO_CHAR.get((e.dx, e.dy), "E")
    for (x, y), (dx, dy, age, _eid) in water.items():
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


def run_headless(duration_ms, level_lines):
    w, h, walls, emitters, sinks = parse_level(level_lines)
    water = {}
    steps = max(1, int(math.ceil(duration_ms / float(STEP_MS))))
    for _ in range(steps):
        tick(w, h, walls, emitters, sinks, water)
    print(f"Simulated {steps} steps (~{duration_ms} ms)")
    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))
