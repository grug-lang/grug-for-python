import grug
from grug.packages import grug_stdlib

state = grug.init(
    packages=[
        grug_stdlib.get(),
    ]
)

state.run_all_package_tests()
