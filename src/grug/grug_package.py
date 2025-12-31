from typing import Sequence

from grug.game_fn import GameFn


class GrugPackage:
    def __init__(self, *, prefix: str, game_fns: Sequence[GameFn]):
        self.prefix = prefix
        self.game_fns = game_fns

    def no_prefix(self):
        self.prefix = ""
        return self

    def set_prefix(self, new_prefix: str):
        self.prefix = new_prefix
        return self
