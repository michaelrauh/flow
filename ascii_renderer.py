from typing import Mapping

from levels import DIR_TO_CHAR, SINK
from simulation_constants import WATER_DIR_CHAR
from simulation_state import WaterCell
from typedefs import Coord


class AsciiRenderer:
    @staticmethod
    def render(
        w: int,
        h: int,
        walls,
        emitters,
        sinks,
        water: Mapping[Coord, WaterCell],
        show_coords: bool = False,
    ) -> str:
        grid = [["." for _ in range(w)] for _ in range(h)]
        for (x, y) in walls:
            grid[y][x] = "#"
        for (x, y) in sinks:
            grid[y][x] = SINK
        for e in emitters:
            grid[e.y][e.x] = DIR_TO_CHAR.get((e.dx, e.dy), "E")
        for (x, y), cell in water.items():
            dx, dy = cell.dx, cell.dy
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
