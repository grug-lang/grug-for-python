import time

import grug
from grug import GrugState

state = grug.init()


@state.game_fn
def print_string(state: GrugState, string: str):
    print(string)


file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()
dog2 = file.create_entity()

while True:
    state.update()
    dog1.bark("woof")
    dog2.bark("arf")
    time.sleep(1)
