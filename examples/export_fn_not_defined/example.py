import grug

state = grug.init()


file = state.compile_grug_file("animals/labrador-Dog.grug")
dog1 = file.create_entity()
dog1.on_nonexistent()
