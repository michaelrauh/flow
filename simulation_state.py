from dataclasses import dataclass, field
from typing import Dict

from typedefs import Coord


@dataclass
class WaterCell:
    dx: int
    dy: int
    age: int
    emitter_id: int
    prefer_left: bool


@dataclass
class SimulationState:
    water: Dict[Coord, WaterCell] = field(default_factory=dict)
    sink_claims: Dict[Coord, int] = field(default_factory=dict)

    def clear_water(self) -> None:
        self.water.clear()

    def clear_sink_claims(self) -> None:
        self.sink_claims.clear()
