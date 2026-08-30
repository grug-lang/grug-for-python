from typing import List

import grug
from grug import GrugPackage, GrugState, HostFn, Type


class VecNumber:
    @staticmethod
    def new(state: GrugState) -> "VecNumber":
        return VecNumber()


class Box:
    @staticmethod
    def of(generics: List[Type]) -> HostFn:
        def inner(state: GrugState, value: float) -> "Box":
            return Box()

        return inner


def magic(state: GrugState) -> float:
    return 42.0


def print_number(state: GrugState, value: float) -> None:
    print(value)


pkg = GrugPackage(
    prefix="",
    host_fns=[print_number],
    generic_fns=[],
    methods=[],
    generic_methods=[],
    static_methods=[("VecNumber", VecNumber.new), ("Dog", magic)],
    generic_static_methods=[("Box", Box.of)],
)

state = grug.init(packages=[pkg])

dog = state.mods["animals"]["labrador-Dog.grug"].create_entity()
dog.bark()
