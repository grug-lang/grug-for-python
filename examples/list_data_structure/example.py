import grug
from grug.packages import grug_stdlib

state = grug.init(
    packages=[
        grug_stdlib.get(),
    ]
)

file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()

dog1.on_run()
