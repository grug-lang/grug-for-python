from typing import Any, List

import grug
from grug import GrugState, HostFn, Type


# A package may carry static methods alongside its methods. This one is
# registered on a class whose name is lowercase, which mod_api.json permits.
class Lowercase:
    items: List[float]


def new(state: GrugState) -> Lowercase:
    vec = Lowercase()
    vec.items = [1.0, 2.0]
    return vec


def length(state: GrugState, receiver: Lowercase) -> float:
    return float(len(receiver.items))


length.__name__ = "len"


def of(generics: List[Type]) -> HostFn:
    def inner(state: GrugState, value: Any) -> Lowercase:
        vec = Lowercase()
        vec.items = [value]
        return vec

    return inner


state = grug.init(
    packages=[
        grug.GrugPackage(
            prefix="",
            host_fns=[],
            generic_fns=[],
            methods=[("vec", length)],
            generic_methods=[],
            static_methods=[("vec", new)],
            generic_static_methods=[("vec", of)],
        )
    ]
)


@state.grug_class
class VecNumber:
    values: List[float]
    capacity: float

    # A static method takes the GrugState as its first argument, where a method
    # takes the receiver first and the state second. That is what tells grug
    # which of the two a Python function is meant to be.
    @staticmethod
    def new(state: GrugState) -> "VecNumber":
        vec = VecNumber()
        vec.values = []
        vec.capacity = 0
        return vec

    @staticmethod
    def with_capacity(state: GrugState, capacity: float) -> "VecNumber":
        vec = VecNumber.new(state)
        vec.capacity = capacity
        return vec

    def push(self, state: GrugState, value: float) -> None:
        self.values.append(value)

    def pop(self, state: GrugState) -> float:
        return self.values.pop()


@state.grug_class
class Box:
    value: Any

    # A generic static method has the same Python signature as a generic
    # method, so which of the two is meant has to be said out loud.
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
    def count(state: GrugState) -> float:
        return 2.0


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
