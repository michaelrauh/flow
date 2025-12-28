from typing import Dict, Iterable, Mapping, Set

from simulation_state import WaterCell
from typedefs import Coord


class WaterPruner:
    @staticmethod
    def prune(next_water: Mapping[Coord, WaterCell], emitters: Iterable) -> Dict[Coord, WaterCell]:
        positions_by_eid: Dict[int, Set[Coord]] = {}
        for position, cell in next_water.items():
            positions_by_eid.setdefault(cell.emitter_id, set()).add(position)

        reachable: Dict[int, Set[Coord]] = {}
        for emitter in emitters:
            positions = positions_by_eid.get(emitter.id, set())
            if not positions:
                continue

            # Keep the connected component that is closest to the emitter. Use the
            # minimum Manhattan-distance tiles as attachment points, then flood
            # through same-emitter water (4-neighbor).
            min_dist = min(abs(nx - emitter.x) + abs(ny - emitter.y) for (nx, ny) in positions)
            seeds = [(nx, ny) for (nx, ny) in positions if abs(nx - emitter.x) + abs(ny - emitter.y) == min_dist]
            stack = list(seeds)
            seen = reachable.setdefault(emitter.id, set())

            while stack:
                pos = stack.pop()
                if pos in seen:
                    continue
                seen.add(pos)
                x, y = pos
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (nx, ny) in positions:
                        stack.append((nx, ny))

        filtered: Dict[Coord, WaterCell] = {}
        for position, cell in next_water.items():
            if position in reachable.get(cell.emitter_id, set()):
                filtered[position] = cell
        return filtered
