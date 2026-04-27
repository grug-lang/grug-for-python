import grug
from grug import GrugState
from grug.entity import GameFnError

state = grug.init()


@state.game_fn
def print_string(state: GrugState, string: str):
    if string == "":
        raise GameFnError("print_string() received an empty string")
    print(string)


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.on_bark("woof")
dog1.on_bark("")
