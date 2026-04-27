import grug
from grug import GrugState

state = grug.init()


@state.game_fn
def spawn(state: GrugState, name: str):
    print(name)


file = state.mods["animals"]["labrador-Dog.grug"]

dog = file.create_entity()

dog.on_tick()
