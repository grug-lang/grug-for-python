import grug
from grug import GrugState

state = grug.init()


@state.game_fn
def open_file(state: GrugState, filename: str):
    print(filename)


file = state.mods["animals"]["labrador-Dog.grug"]

dog = file.create_entity()

dog.on_tick()
