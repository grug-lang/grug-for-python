import grug
from grug.packages import grug_numpy, grug_stdlib

state = grug.init(
    packages=[
        grug_stdlib.get(),
        grug_numpy.get(),
    ]
)

state.run_all_package_tests()
