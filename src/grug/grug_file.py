from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional

from grug.game_fn import GameFn
from grug.parser import HelperFn, OnFn, VariableStatement

if TYPE_CHECKING:
    from grug.grug_state import GrugState


@dataclass
class GrugFile:
    relative_path: str
    mod: str

    global_variables: List[VariableStatement]
    on_fns: Dict[str, OnFn]
    helper_fns: Dict[str, HelperFn]
    game_fns: Dict[str, GameFn]
    game_fn_return_types: Dict[str, Optional[str]]

    state: GrugState

    def create_entity(self):
        from grug.entity import Entity

        return Entity(self)
