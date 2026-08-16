import grug
from grug import GrugState, Type, HostFn
from typing import List

state = grug.init()


@state.grug_class
class Printer:
    def print_string(self, state: GrugState, string: str):
        print(self)
        print(string)

    @staticmethod
    def print(ty: List[Type]) -> HostFn:
        def inner(self: Printer, state: GrugState, obj: object):
            print(type(obj))
            print(self)
            print(obj)
        
        return inner


@state.host_fn
def printer(state: GrugState) -> Printer:
    return Printer()


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
