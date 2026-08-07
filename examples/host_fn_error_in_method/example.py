import grug
from grug import GrugState
from grug.entity import GameFnError

state = grug.init()


class Printer:
    @state.host_method
    @staticmethod
    def print_string(state: GrugState, instance: int, string: str):
        if string == "":
            raise GameFnError("Printer.print_string() received an empty string")
        print(string)
        


@state.host_fn
def printer(state: GrugState):
    return 42


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
dog1.bark("")
