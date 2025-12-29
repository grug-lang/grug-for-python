import time

import grug
from grug.packages import grug_numpy, grug_stdlib

state = grug.init(
    packages=[
        grug_stdlib.get().noprefix(),
        grug_numpy.get(),
    ]
)

file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()

while True:
    state.update()
    dog1.on_tick()
    time.sleep(1)
