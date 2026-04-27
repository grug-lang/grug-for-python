import grug

state = grug.init()


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()
dog1.on_nonexistent()
