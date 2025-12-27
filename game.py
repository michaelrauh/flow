import pygame

from graphics import TILE, WallSprite, build_static_sprites, sync_water_sprites
from levels import LEVEL_ORDER, LEVELS, get_level, parse_level
from simulation import STEP_MS, render_ascii, tick

FPS = 60


def run_game(initial_level="turn"):
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

    current_level = initial_level
    w = h = 0
    walls = set()
    emitters = []
    sinks = set()
    emitter_positions = set()
    static_sprites = pygame.sprite.Group()
    wall_lookup = {}
    water = {}
    water_sprites = pygame.sprite.Group()
    screen = None
    font = pygame.font.SysFont(None, 14)
    clock = pygame.time.Clock()

    def load_level(name):
        nonlocal w, h, walls, emitters, sinks, emitter_positions, static_sprites, wall_lookup, current_level, screen
        current_level = name
        level_lines = get_level(name)
        w, h, walls, emitters, sinks = parse_level(level_lines)
        emitter_positions = {(e.x, e.y) for e in emitters}
        static_sprites, wall_lookup = build_static_sprites(walls, sinks, emitters)
        water.clear()
        water_sprites.empty()
        screen = pygame.display.set_mode((w * TILE, h * TILE))

    load_level(current_level)
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
                elif event.key == pygame.K_p:
                    print(render_ascii(w, h, walls, emitters, sinks, water, show_coords=True))
                elif event.key in level_hotkeys:
                    load_level(level_hotkeys[event.key])
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
