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
from simulation import STEP_MS, SimulationState, clear_sink_claims, render_ascii, tick

FPS = 60
GAME_SPEED = 5.0  # multiplier on simulation speed in the interactive view


class InputMode:
    def __init__(self, emitter_dirs):
        self.emitter_dirs = list(emitter_dirs)
        self.dir_index = 1 if (1, 0) in self.emitter_dirs else 0  # default to right if present
        self.placement_mode = "wall"

    def set_mode(self, mode: str) -> bool:
        if mode not in ("wall", "sink", "emitter"):
            return False
        if mode == self.placement_mode:
            return False
        self.placement_mode = mode
        return True

    def rotate(self) -> None:
        self.dir_index = (self.dir_index + 1) % len(self.emitter_dirs)

    def current_dir(self):
        return self.emitter_dirs[self.dir_index]

    def dir_label(self) -> str:
        dx, dy = self.current_dir()
        return DIR_TO_CHAR.get((dx, dy), f"{dx},{dy}")


class LevelState:
    def __init__(self, initial_level: str):
        self.current_level = initial_level
        self.w = 0
        self.h = 0
        self.walls = set()
        self.emitters = []
        self.emitter_positions = set()
        self.emitter_map = {}
        self.emitter_colors = {}
        self.sinks = set()
        self.next_emitter_id = 0
        self.load(initial_level)

    def load(self, name: str) -> None:
        self.current_level = name
        level_lines = get_level(name)
        self.w, self.h, self.walls, self.emitters, self.sinks = parse_level(level_lines)
        self.emitter_positions = {(e.x, e.y) for e in self.emitters}
        self.emitter_map = {(e.x, e.y): e for e in self.emitters}
        self.emitter_colors = {e.id: emitter_color_for_id(e.id) for e in self.emitters}
        self.next_emitter_id = (max((e.id for e in self.emitters), default=-1) + 1)

    def _blocked(self, gx, gy) -> bool:
        return (gx, gy) in self.sinks or (gx, gy) in self.emitter_positions

    def toggle_wall(self, gx, gy):
        if self._blocked(gx, gy):
            return None
        if (gx, gy) in self.walls:
            self.walls.remove((gx, gy))
            return "removed"
        self.walls.add((gx, gy))
        return "added"

    def place_wall(self, gx, gy):
        if self._blocked(gx, gy) or (gx, gy) in self.walls:
            return None
        self.walls.add((gx, gy))
        return "added"

    def toggle_sink(self, gx, gy):
        if (gx, gy) in self.emitter_positions or (gx, gy) in self.walls:
            return None
        if (gx, gy) in self.sinks:
            self.sinks.remove((gx, gy))
            return "removed"
        self.sinks.add((gx, gy))
        return "added"

    def place_sink(self, gx, gy):
        if (gx, gy) in self.sinks or (gx, gy) in self.emitter_positions or (gx, gy) in self.walls:
            return None
        self.sinks.add((gx, gy))
        return "added"

    def _add_emitter(self, gx, gy, direction):
        dx, dy = direction
        emitter = Emitter(self.next_emitter_id, gx, gy, dx, dy)
        self.next_emitter_id += 1
        self.emitters.append(emitter)
        self.emitter_positions.add((gx, gy))
        self.emitter_map[(gx, gy)] = emitter
        self.emitter_colors[emitter.id] = emitter_color_for_id(emitter.id)
        return emitter

    def _remove_emitter(self, gx, gy):
        emitter = self.emitter_map.pop((gx, gy), None)
        if emitter is None:
            return None
        self.emitters[:] = [e for e in self.emitters if e.id != emitter.id]
        self.emitter_positions.discard((gx, gy))
        self.emitter_colors.pop(emitter.id, None)
        return emitter

    def toggle_emitter(self, gx, gy, direction):
        if (gx, gy) in self.walls or (gx, gy) in self.sinks:
            return None, None
        if (gx, gy) in self.emitter_positions:
            emitter = self._remove_emitter(gx, gy)
            return "removed", emitter
        emitter = self._add_emitter(gx, gy, direction)
        return "added", emitter

    def place_emitter(self, gx, gy, direction):
        if (gx, gy) in self.walls or (gx, gy) in self.sinks or (gx, gy) in self.emitter_positions:
            return None, None
        emitter = self._add_emitter(gx, gy, direction)
        return "added", emitter


class ViewContext:
    def __init__(self, header_height: int):
        self.header_height = header_height
        self.static_sprites = pygame.sprite.Group()
        self.wall_lookup = {}
        self.sink_lookup = {}
        self.emitter_lookup = {}
        self.screen = None

    def create_screen(self, w, h):
        self.screen = pygame.display.set_mode((w * TILE, h * TILE + self.header_height))

    def rebuild_static(self, level: LevelState):
        self.static_sprites, self.wall_lookup, self.sink_lookup, self.emitter_lookup = build_static_sprites(
            level.walls, level.sinks, level.emitters, level.emitter_colors
        )

    def add_wall(self, gx, gy):
        sprite = WallSprite(gx, gy)
        self.wall_lookup[(gx, gy)] = sprite
        self.static_sprites.add(sprite)

    def remove_wall(self, gx, gy):
        sprite = self.wall_lookup.pop((gx, gy), None)
        if sprite:
            sprite.kill()

    def add_sink(self, gx, gy):
        sprite = SinkSprite(gx, gy)
        self.sink_lookup[(gx, gy)] = sprite
        self.static_sprites.add(sprite)

    def remove_sink(self, gx, gy):
        sprite = self.sink_lookup.pop((gx, gy), None)
        if sprite:
            sprite.kill()

    def add_emitter(self, emitter):
        color = emitter_color_for_id(emitter.id)
        sprite = EmitterSprite(emitter, color)
        self.emitter_lookup[(emitter.x, emitter.y)] = (emitter, sprite)
        self.static_sprites.add(sprite)

    def remove_emitter(self, gx, gy):
        existing = self.emitter_lookup.pop((gx, gy), None)
        if existing:
            _emitter, sprite = existing
            sprite.kill()


class WaterState:
    def __init__(self):
        self.sim_state = SimulationState()
        self.water_sprites = pygame.sprite.Group()

    def clear(self):
        self.sim_state.clear_water()
        self.water_sprites.empty()

    def clear_at(self, gx, gy):
        self.sim_state.water.pop((gx, gy), None)

    def step(self, level: LevelState):
        tick(level.w, level.h, level.walls, level.emitters, level.sinks, self.sim_state)

    def sync(self, level: LevelState):
        sync_water_sprites(self.sim_state.water, self.water_sprites, level.emitter_colors)


def run_game(initial_level: str = "empty") -> None:
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
    number_keys = [
        pygame.K_1,
        pygame.K_2,
        pygame.K_3,
        pygame.K_4,
        pygame.K_5,
        pygame.K_6,
        pygame.K_7,
        pygame.K_8,
        pygame.K_9,
        pygame.K_0,
    ]
    level_hotkeys = {key: name for key, name in zip(number_keys, level_order)}

    instructions = [
        "Space: pause/resume | N: step | R: reset water | P: print map | M: print map (no water) | 1-9,0: change level",
        "Modes: W wall | S sink | E emitter (tap again to rotate) | Left-click place/remove | Right-click clear water",
    ]
    header_font = pygame.font.SysFont(None, 16)
    header_pad = 4
    header_height = header_font.get_linesize() * len(instructions) + header_pad * 2
    font = pygame.font.SysFont(None, 14)
    clock = pygame.time.Clock()

    input_mode = InputMode(DIRS.values())
    level_state = LevelState(initial_level)
    view = ViewContext(header_height)
    view.create_screen(level_state.w, level_state.h)
    view.rebuild_static(level_state)
    water_state = WaterState()

    step_acc = 0
    running = True
    paused = False

    def update_caption():
        pygame.display.set_caption(
            f"Flow - mode: {input_mode.placement_mode} (Emitter dir: {input_mode.dir_label()})"
        )

    def clear_water_state():
        water_state.clear()

    def reset_sink_claims():
        clear_sink_claims(water_state.sim_state)

    def load_level(name):
        reset_sink_claims()
        level_state.load(name)
        view.create_screen(level_state.w, level_state.h)
        view.rebuild_static(level_state)
        clear_water_state()
        update_caption()

    def handle_wall(gx, gy, toggle=True):
        action = level_state.toggle_wall(gx, gy) if toggle else level_state.place_wall(gx, gy)
        if action == "added":
            view.add_wall(gx, gy)
            clear_water_state()
        elif action == "removed":
            view.remove_wall(gx, gy)
            clear_water_state()

    def handle_sink(gx, gy, toggle=True):
        action = level_state.toggle_sink(gx, gy) if toggle else level_state.place_sink(gx, gy)
        if action == "added":
            view.add_sink(gx, gy)
            clear_water_state()
        elif action == "removed":
            view.remove_sink(gx, gy)
            clear_water_state()

    def handle_emitter(gx, gy, toggle=True):
        direction = input_mode.current_dir()
        action, emitter = (
            level_state.toggle_emitter(gx, gy, direction)
            if toggle
            else level_state.place_emitter(gx, gy, direction)
        )
        if action == "added" and emitter:
            view.add_emitter(emitter)
            clear_water_state()
        elif action == "removed":
            view.remove_emitter(gx, gy)
            clear_water_state()

    def apply_action(gx, gy, toggle=True):
        if input_mode.placement_mode == "wall":
            handle_wall(gx, gy, toggle)
        elif input_mode.placement_mode == "sink":
            handle_sink(gx, gy, toggle)
        elif input_mode.placement_mode == "emitter":
            handle_emitter(gx, gy, toggle)

    def clear_water_at(gx, gy):
        water_state.clear_at(gx, gy)

    def step_simulation():
        water_state.step(level_state)

    def sync_water():
        water_state.sync(level_state)

    update_caption()

    while running:
        dt = clock.tick(FPS)
        step_acc += dt * GAME_SPEED

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_n:
                    step_simulation()
                elif event.key == pygame.K_r:
                    clear_water_state()
                elif event.key == pygame.K_w:
                    if input_mode.set_mode("wall"):
                        update_caption()
                elif event.key == pygame.K_s:
                    if input_mode.set_mode("sink"):
                        update_caption()
                elif event.key == pygame.K_e:
                    if input_mode.placement_mode == "emitter":
                        input_mode.rotate()
                    else:
                        if input_mode.set_mode("emitter"):
                            update_caption()
                    update_caption()
                elif event.key == pygame.K_m:
                    print(
                        render_ascii(
                            level_state.w, level_state.h, level_state.walls, level_state.emitters, level_state.sinks, {}, show_coords=True
                        )
                    )
                elif event.key == pygame.K_p:
                    print(
                        render_ascii(
                            level_state.w,
                            level_state.h,
                            level_state.walls,
                            level_state.emitters,
                            level_state.sinks,
                            water_state.sim_state.water,
                            show_coords=True,
                        )
                    )
                elif event.key in level_hotkeys:
                    load_level(level_hotkeys[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if my < header_height:
                    continue
                gx, gy = mx // TILE, (my - header_height) // TILE
                if not (0 <= gx < level_state.w and 0 <= gy < level_state.h):
                    continue
                if event.button == 1:
                    apply_action(gx, gy, toggle=True)
                elif event.button == 3:
                    clear_water_at(gx, gy)
            elif event.type == pygame.MOUSEMOTION:
                mx, my = pygame.mouse.get_pos()
                if my < header_height:
                    continue
                gx, gy = mx // TILE, (my - header_height) // TILE
                if not (0 <= gx < level_state.w and 0 <= gy < level_state.h):
                    continue
                buttons = pygame.mouse.get_pressed()
                if buttons[0]:
                    apply_action(gx, gy, toggle=False)
                elif buttons[2]:
                    clear_water_at(gx, gy)

        if not paused:
            while step_acc >= STEP_MS:
                step_acc -= STEP_MS
                step_simulation()

        sync_water()

        screen = view.screen
        screen.fill((20, 20, 20))
        pygame.draw.rect(screen, (30, 30, 30), (0, 0, level_state.w * TILE, header_height))
        for idx, line in enumerate(instructions):
            text = header_font.render(line, True, (200, 200, 200))
            screen.blit(text, (4, header_pad + idx * header_font.get_linesize()))

        grid_surface = screen.subsurface((0, header_height, level_state.w * TILE, level_state.h * TILE))
        grid_surface.fill((20, 20, 20))
        view.static_sprites.draw(grid_surface)
        water_state.water_sprites.draw(grid_surface)
        draw_coords(grid_surface, level_state.w, level_state.h, font)

        pygame.display.flip()

    pygame.quit()
