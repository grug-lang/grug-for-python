import grug
from grug import GrugState
from grug.entity import GameFnError

state = grug.init()


@state.grug_class
class Printer:
    @staticmethod
    def print_string(state: GrugState, instance: int, string: str):
        if string == "":
            raise GameFnError("Printer.print_string() received an empty string")
        print(string)


@state.game_fn
def printer(state: GrugState):
    return 42


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
dog1.bark("")
