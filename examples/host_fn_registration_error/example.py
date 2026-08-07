import grug
from grug import GrugState
from grug.entity import GameFnError

state = grug.init()

@state.host_fn
def print_string(state: GrugState, string: str):
    if string == "":
        raise GameFnError("print_string() received an empty string")
    print(string)

def print_string_2(state: GrugState, string: str):
    if string == "":
        raise GameFnError("print_string() received an empty string")
    print(string)

print_string_2.__name__ = "print_string"
state.host_fn(print_string_2)

file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
dog1.bark("")
