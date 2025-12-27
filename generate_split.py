"""
Generate a recursively split map with 1-tile corridors and single openings per wall.

The algorithm uses recursive division on an odd-sized grid: every division draws a
wall down the middle of a region and leaves a single opening, then recurses on the
two subregions until they are too small to divide further. This produces a fully
connected maze-like layout where every corridor is 1 tile wide.
"""

from __future__ import annotations

from typing import List


def choose_mid(values: List[int]) -> int:
    return values[len(values) // 2]


def make_split_map(width: int = 45, height: int = 21) -> List[str]:
    if width % 2 == 0 or height % 2 == 0:
        raise ValueError("Width and height must be odd to keep corridors 1 tile wide.")

    grid = [["." for _ in range(width)] for _ in range(height)]
    for x in range(width):
        grid[0][x] = "#"
        grid[height - 1][x] = "#"
    for y in range(height):
        grid[y][0] = "#"
        grid[y][width - 1] = "#"

    def divide(x0: int, y0: int, x1: int, y1: int) -> None:
        # Region is between the boundary walls at (x0,y0) inclusive and (x1,y1) inclusive.
        # Only divide if there's room for a wall with openings on both sides.
        w = x1 - x0
        h = y1 - y0
        if w < 4 or h < 4:
            return

        if w > h:
            orientation = "vertical"
        elif h > w:
            orientation = "horizontal"
        else:
            orientation = "vertical"

        if orientation == "vertical":
            possible_walls = [x for x in range(x0 + 2, x1, 2)]
            if not possible_walls:
                return
            wall_x = choose_mid(possible_walls)
            possible_gaps = [y for y in range(y0 + 1, y1) if y % 2 == 1]
            gap_y = choose_mid(possible_gaps)

            for y in range(y0 + 1, y1):
                grid[y][wall_x] = "#"
            grid[gap_y][wall_x] = "."

            divide(x0, y0, wall_x, y1)
            divide(wall_x, y0, x1, y1)
        else:
            possible_walls = [y for y in range(y0 + 2, y1, 2)]
            if not possible_walls:
                return
            wall_y = choose_mid(possible_walls)
            possible_gaps = [x for x in range(x0 + 1, x1) if x % 2 == 1]
            gap_x = choose_mid(possible_gaps)

            for x in range(x0 + 1, x1):
                grid[wall_y][x] = "#"
            grid[wall_y][gap_x] = "."

            divide(x0, y0, x1, wall_y)
            divide(x0, wall_y, x1, y1)

    divide(0, 0, width - 1, height - 1)
    return ["".join(row) for row in grid]


if __name__ == "__main__":
    for line in make_split_map():
        print(line)
