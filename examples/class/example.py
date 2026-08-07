import grug
from grug import GrugState, Type
from typing import List

state = grug.init()


@state.grug_class
class Printer:
    def print_string(state: GrugState, instance: int, string: str):
        print(instance)
        print(string)

    def print(ty: List[Type]):
        def inner(state: GrugState, instance: int, obj: object):
            print(type(obj))
            print(instance)
            print(obj)
        
        return inner


@state.host_fn
def printer(state: GrugState):
    return 42


file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

state.update()
dog1.bark("woof")
