from pathlib import Path

import grug
from grug import GrugState

state = grug.init()


@state.host_fn
def print_string(state: GrugState, string: str):
    print(string)


file = state.mods["animals"]["labrador-Dog.grug"]
dog = file.create_entity()

print("Writing mods/animals/foo.txt...")
resource_path = Path("mods/animals/foo.txt")
resource_path.write_text("Hello, world!")

state.update()

assert state.updated_resources
print("Detected updated resources:")
for res in state.updated_resources:
    print(f" - {res}")

print("Deleting foo.txt...")
resource_path.unlink()

dog.bark("woof")
