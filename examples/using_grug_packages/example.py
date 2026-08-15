import time

import grug
from grug.packages import grug_numpy, grug_stdlib
from grug import GrugPackage

class Printer:
    @staticmethod
    def print_string(state: GrugState, self, string: str):
        print(string)


def printer(state: GrugState) -> Printer:
    return Printer()

my_package = GrugPackage(
    prefix="",
    host_fns=[printer],
    generic_fns=[],
    methods=[("Printer", Printer.print_string)],
    generic_methods=[],
)


state = grug.init(
    packages=[
        grug_stdlib.get(),
        grug_numpy.get(),
        my_package,
    ]
)

file = state.mods["animals"]["labrador-Dog.grug"]

dog1 = file.create_entity()

while True:
    state.update()
    dog1.tick()
    time.sleep(1)
