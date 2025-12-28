import colorsys
from typing import Mapping

import pygame

from simulation_state import WaterCell
from typedefs import Coord

TILE = 24

_WALL_SURFACE = None
_SINK_SURFACE_CACHE = {}
_EMITTER_SURFACE_CACHE = {}
_WATER_SURFACE_CACHE = {}
_DEFAULT_SINK_DOT = (20, 10, 10)


def _make_surface(color):
    surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    surface.fill(color)
    return surface


def _darken(color, factor=0.6):
    r, g, b = color
    return (int(r * factor), int(g * factor), int(b * factor))


def _lighten(color, factor=1.2):
    r, g, b = color
    return tuple(min(255, int(c * factor)) for c in (r, g, b))


def emitter_color_for_id(eid):
    # Evenly distribute hues using golden ratio to avoid clustering.
    hue = (eid * 0.61803398875) % 1.0
    sat = 0.75
    val = 0.95
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return (int(r * 255), int(g * 255), int(b * 255))


def get_wall_surface():
    global _WALL_SURFACE
    if _WALL_SURFACE is None:
        _WALL_SURFACE = _make_surface((80, 80, 80))
    return _WALL_SURFACE


def get_sink_surface(dot_color=None):
    color = dot_color if dot_color is not None else _DEFAULT_SINK_DOT
    surface = _SINK_SURFACE_CACHE.get(color)
    if surface is None:
        surface = _make_surface((70, 30, 30))
        center = (TILE // 2, TILE // 2)
        pygame.draw.circle(surface, color, center, TILE // 4)
        _SINK_SURFACE_CACHE[color] = surface
    return surface


def get_emitter_surface(dx, dy, color):
    key = (dx, dy, color)
    if key not in _EMITTER_SURFACE_CACHE:
        surface = _make_surface(color)
        center = (TILE // 2, TILE // 2)
        arrow_end = (
            center[0] + dx * (TILE // 3),
            center[1] + dy * (TILE // 3),
        )
        pygame.draw.line(surface, _darken(color, 0.5), center, arrow_end, 3)
        _EMITTER_SURFACE_CACHE[key] = surface
    return _EMITTER_SURFACE_CACHE[key]


def get_water_surface(dx, dy, color):
    key = (dx, dy, color)
    if key not in _WATER_SURFACE_CACHE:
        surface = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        center = (TILE // 2, TILE // 2)
        pygame.draw.circle(surface, color, center, TILE // 3)
        arrow_end = (
            center[0] + dx * (TILE // 2 - 3),
            center[1] + dy * (TILE // 2 - 3),
        )
        pygame.draw.line(surface, _lighten(color, 1.25), center, arrow_end, 3)
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
        self.dot_color = None
        super().__init__(x, y, get_sink_surface())

    def set_dot_color(self, dot_color):
        if dot_color == self.dot_color:
            return
        self.dot_color = dot_color
        self.image = get_sink_surface(dot_color)


class EmitterSprite(TileSprite):
    def __init__(self, emitter, color):
        super().__init__(emitter.x, emitter.y, get_emitter_surface(emitter.dx, emitter.dy, color))


class WaterSprite(TileSprite):
    def __init__(self, x, y, dx, dy, color):
        super().__init__(x, y, get_water_surface(dx, dy, color))
        self.dx = dx
        self.dy = dy
        self.color = color

    def update_state(self, x, y, dx, dy, color):
        if (dx, dy) != (self.dx, self.dy) or color != self.color:
            self.image = get_water_surface(dx, dy, color)
        self.dx, self.dy = dx, dy
        self.color = color
        if (x, y) != self.grid_pos:
            self.grid_pos = (x, y)
            self.rect.topleft = (x * TILE, y * TILE)


def build_static_sprites(walls, sinks, emitters, emitter_colors):
    static_sprites = pygame.sprite.Group()
    wall_lookup = {}
    sink_lookup = {}
    emitter_lookup = {}

    for (x, y) in walls:
        sprite = WallSprite(x, y)
        wall_lookup[(x, y)] = sprite
        static_sprites.add(sprite)
    for (x, y) in sinks:
        sprite = SinkSprite(x, y)
        sink_lookup[(x, y)] = sprite
        static_sprites.add(sprite)
    for emitter in emitters:
        color = emitter_colors.get(emitter.id)
        if color is None:
            color = emitter_color_for_id(emitter.id)
        sprite = EmitterSprite(emitter, color)
        emitter_lookup[(emitter.x, emitter.y)] = (emitter, sprite)
        static_sprites.add(sprite)
    return static_sprites, wall_lookup, sink_lookup, emitter_lookup


def sync_water_sprites(
    water_state: Mapping[Coord, WaterCell],
    water_group,
    emitter_colors,
):
    existing = {(sprite.grid_pos): sprite for sprite in water_group.sprites()}
    missing = set(existing.keys()) - set(water_state.keys())
    for pos in missing:
        existing[pos].kill()
        existing.pop(pos, None)

    for (x, y), cell in water_state.items():
        dx, dy, eid = cell.dx, cell.dy, cell.emitter_id
        color = emitter_colors.get(eid, emitter_color_for_id(eid))
        sprite = existing.get((x, y))
        if sprite is None:
            water_group.add(WaterSprite(x, y, dx, dy, color))
        else:
            sprite.update_state(x, y, dx, dy, color)


def sync_sink_sprites(sink_lookup, sink_claims, emitter_colors):
    for pos, sprite in sink_lookup.items():
        owner = sink_claims.get(pos)
        dot_color = None
        if owner is not None:
            dot_color = emitter_colors.get(owner, emitter_color_for_id(owner))
        sprite.set_dot_color(dot_color)
