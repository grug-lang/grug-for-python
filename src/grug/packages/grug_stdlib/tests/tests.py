import grug
from grug.grug_dir import GrugDir
from grug.packages import grug_stdlib

state = grug.init(
    packages=[
        grug_stdlib.get(),
    ]
)

mods = state.compile_all_mods()


def run(dir: GrugDir):
    for subdir in dir.dirs.values():
        run(subdir)
    for file in dir.files.values():
        test = file.create_entity()
        test.on_run()


run(mods)
