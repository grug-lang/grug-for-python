import grug
from grug.grug_state import GrugState

state = grug.init()


@state.game_fn
def print_string(state: GrugState, string: str):
    print(string)  # pragma: no cover


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()
dog1.on_nonexistent()
