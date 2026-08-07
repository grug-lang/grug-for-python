from grug import GrugState
import grug

state = grug.init()

@state.host_fn
def print_string(state: GrugState, string: str):
    print(str)

state.mods["animals"]["foo"]
