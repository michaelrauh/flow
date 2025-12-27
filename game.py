import pygame

from graphics import (
    TILE,
    EmitterSprite,
    SinkSprite,
    WallSprite,
    build_static_sprites,
    emitter_color_for_id,
    sync_water_sprites,
)
from levels import DIRS, DIR_TO_CHAR, Emitter, LEVEL_ORDER, LEVELS, get_level, parse_level
from simulation import STEP_MS, render_ascii, tick

FPS = 60


def run_game(initial_level="empty"):
    def draw_coords(surface, w, h, font):
        color = (140, 140, 140)
        for x in range(w):
            label = font.render(str(x % 10), True, color)
            surface.blit(label, (x * TILE + 4, 2))
        for y in range(h):
            label = font.render(str(y), True, color)
            surface.blit(label, (2, y * TILE + 2))

    pygame.init()
    level_order = [name for name in LEVEL_ORDER if name in LEVELS] + [name for name in LEVELS if name not in LEVEL_ORDER]
    level_hotkeys = {getattr(pygame, f"K_{idx+1}"): name for idx, name in enumerate(level_order[:9])}

    emitter_dirs = list(DIRS.values())
    dir_index = 1 if (1, 0) in emitter_dirs else 0  # default to right if present
    placement_mode = "wall"  # wall | sink | emitter
    instructions = [
        "Space: pause/resume | N: step | R: reset water | P: print map | 1-9: change level",
        "Modes: W wall | S sink | E emitter (tap again to rotate) | Left-click place/remove | Right-click clear water",
    ]
    header_font = pygame.font.SysFont(None, 16)
    header_pad = 4
    header_height = header_font.get_linesize() * len(instructions) + header_pad * 2
    current_level = initial_level
    w = h = 0
    walls = set()
    emitters = []
    sinks = set()
    emitter_positions = set()
    static_sprites = pygame.sprite.Group()
    wall_lookup = {}
    sink_lookup = {}
    emitter_lookup = {}
    emitter_colors = {}
    water = {}
    water_sprites = pygame.sprite.Group()
    screen = None
    font = pygame.font.SysFont(None, 14)
    clock = pygame.time.Clock()
    next_emitter_id = 0

    def emitter_dir_label():
        dx, dy = emitter_dirs[dir_index]
        return DIR_TO_CHAR.get((dx, dy), f"{dx},{dy}")

    def update_caption():
        pygame.display.set_caption(
            f"Flow - mode: {placement_mode} (Emitter dir: {emitter_dir_label()})"
        )

    def load_level(name):
        nonlocal w, h, walls, emitters, sinks, emitter_positions, static_sprites, wall_lookup, sink_lookup, emitter_lookup, emitter_colors, current_level, screen, next_emitter_id
        current_level = name
        level_lines = get_level(name)
        w, h, walls, emitters, sinks = parse_level(level_lines)
        emitter_positions = {(e.x, e.y) for e in emitters}
        emitter_colors = {e.id: emitter_color_for_id(e.id) for e in emitters}
        static_sprites, wall_lookup, sink_lookup, emitter_lookup = build_static_sprites(walls, sinks, emitters, emitter_colors)
        next_emitter_id = (max((e.id for e in emitters), default=-1) + 1)
        water.clear()
        water_sprites.empty()
        screen = pygame.display.set_mode((w * TILE, h * TILE + header_height))
        update_caption()

    load_level(current_level)
    step_acc = 0
    running = True
    paused = False

    def toggle_wall(gx, gy):
        if (gx, gy) in emitter_positions or (gx, gy) in sinks:
            return
        if (gx, gy) in walls:
            walls.remove((gx, gy))
            sprite = wall_lookup.pop((gx, gy), None)
            if sprite:
                sprite.kill()
            water.pop((gx, gy), None)
        else:
            walls.add((gx, gy))
            sprite = WallSprite(gx, gy)
            wall_lookup[(gx, gy)] = sprite
            static_sprites.add(sprite)
            water.pop((gx, gy), None)

    def toggle_sink(gx, gy):
        if (gx, gy) in emitter_positions or (gx, gy) in walls:
            return
        if (gx, gy) in sinks:
            sinks.remove((gx, gy))
            sprite = sink_lookup.pop((gx, gy), None)
            if sprite:
                sprite.kill()
            water.pop((gx, gy), None)
        else:
            sinks.add((gx, gy))
            sprite = SinkSprite(gx, gy)
            sink_lookup[(gx, gy)] = sprite
            static_sprites.add(sprite)
            water.pop((gx, gy), None)

    def toggle_emitter(gx, gy):
        nonlocal next_emitter_id
        if (gx, gy) in walls or (gx, gy) in sinks:
            return
        existing = emitter_lookup.pop((gx, gy), None)
        if existing:
            emitter, sprite = existing
            sprite.kill()
            emitters[:] = [e for e in emitters if e.id != emitter.id]
            emitter_positions.discard((gx, gy))
            emitter_colors.pop(emitter.id, None)
            water.pop((gx, gy), None)
        else:
            dx, dy = emitter_dirs[dir_index]
            emitter = Emitter(next_emitter_id, gx, gy, dx, dy)
            next_emitter_id += 1
            emitters.append(emitter)
            emitter_positions.add((gx, gy))
            color = emitter_color_for_id(emitter.id)
            emitter_colors[emitter.id] = color
            sprite = EmitterSprite(emitter, color)
            emitter_lookup[(gx, gy)] = (emitter, sprite)
            static_sprites.add(sprite)
            water.pop((gx, gy), None)

    def rotate_emitter_dir():
        nonlocal dir_index
        dir_index = (dir_index + 1) % len(emitter_dirs)
        update_caption()

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
                elif event.key == pygame.K_w:
                    placement_mode = "wall"
                    update_caption()
                elif event.key == pygame.K_s:
                    placement_mode = "sink"
                    update_caption()
                elif event.key == pygame.K_e:
                    if placement_mode == "emitter":
                        rotate_emitter_dir()
                    else:
                        placement_mode = "emitter"
                        update_caption()
                elif event.key == pygame.K_p:
                    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))
                elif event.key in level_hotkeys:
                    load_level(level_hotkeys[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if my < header_height:
                    continue
                gx, gy = mx // TILE, (my - header_height) // TILE
                if not (0 <= gx < w and 0 <= gy < h):
                    continue
                if event.button == 1:
                    if placement_mode == "wall":
                        toggle_wall(gx, gy)
                    elif placement_mode == "sink":
                        toggle_sink(gx, gy)
                    elif placement_mode == "emitter":
                        toggle_emitter(gx, gy)
                elif event.button == 3:
                    water.pop((gx, gy), None)

        if not paused:
            while step_acc >= STEP_MS:
                step_acc -= STEP_MS
                tick(w, h, walls, emitters, sinks, water)

        sync_water_sprites(water, water_sprites, emitter_colors)

        screen.fill((20, 20, 20))
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, w * TILE, header_height))
        for idx, line in enumerate(instructions):
            text = header_font.render(line, True, (200, 200, 200))
            screen.blit(text, (4, header_pad + idx * header_font.get_linesize()))

        grid_surface = screen.subsurface((0, header_height, w * TILE, h * TILE))
        grid_surface.fill((20, 20, 20))
        static_sprites.draw(grid_surface)
        water_sprites.draw(grid_surface)
        draw_coords(grid_surface, w, h, font)

        pygame.display.flip()

    pygame.quit()
