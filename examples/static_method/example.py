from typing import Any, List

import grug
from grug import GrugState, HostFn, Type

state = grug.init()


@state.grug_class
class VecNumber:
    values: List[float]
    capacity: float

    @staticmethod
    def new(state: GrugState) -> "VecNumber":
        vec = VecNumber()
        vec.values = []
        vec.capacity = 0
        return vec

    def push(self, state: GrugState, value: float) -> None:
        self.values.append(value)

    def pop(self, state: GrugState) -> float:
        return self.values.pop()


@state.grug_class
class Box:
    value: Any

    @grug.static_method
    @staticmethod
    def of(generics: List[Type]) -> HostFn:
        def inner(state: GrugState, value: Any) -> "Box":
            box = Box()
            box.value = value
            return box

        return inner

    @staticmethod
    def get(generics: List[Type]) -> HostFn:
        def inner(self: "Box", state: GrugState) -> Any:
            return self.value

        return inner


@state.grug_class
class Dog:
    @grug.static_method
    @staticmethod
    def magic(state: GrugState) -> float:
        return 42.0


@state.host_fn
def print_number(state: GrugState, value: float) -> None:
    print(value)


@state.host_fn
def print_string(state: GrugState, value: str) -> None:
    print(value)


file = state.mods["animals"]["labrador-Dog.grug"]
dog = file.create_entity()

state.update()
dog.bark("woof")
