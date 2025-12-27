import pygame

TILE = 24

_WALL_SURFACE = None
_SINK_SURFACE = None
_EMITTER_SURFACE_CACHE = {}
_WATER_SURFACE_CACHE = {}


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
