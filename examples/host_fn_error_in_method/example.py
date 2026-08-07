import grug
from grug import GrugState
from grug.entity import GameFnError

state = grug.init()


@state.grug_class
class Printer:
    def print_string(self, state: GrugState, string: str):
        if string == "":
            raise GameFnError("Printer.print_string() received an empty string")
        print(string)
        


@state.host_fn
def printer(state: GrugState):
    return Printer()


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
dog1.bark("")
