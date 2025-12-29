from dataclasses import dataclass
from typing import Sequence

from grug.game_fn import GameFn


@dataclass
class GrugPackage:
    prefix: str
    game_fns: Sequence[GameFn]

    def __post_init__(self):
        if not self.prefix:
            raise ValueError("GrugPackage.prefix must be non-empty")

    def noprefix(self):
        self.prefix = ""
        return self
