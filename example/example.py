import grug
import time

state = grug.init()

@state.game_fn
def print_string(string: str):
    print(string)

file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()
dog2 = file.create_entity()

while True:
    state.update()
    dog1.on_bark("woof")
    dog2.on_bark("arf")
    time.sleep(1)
