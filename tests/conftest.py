import ctypes
from pathlib import Path
import pytest

# --------------------------------------------------------------------------
# C callback type definitions
# --------------------------------------------------------------------------

compile_grug_file_t = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
init_globals_fn_dispatcher_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
on_fn_dispatcher_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t) # TODO: Change this ctypes.c_void_p to `struct grug_value values[]`
dump_file_to_json_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
generate_file_from_json_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
game_fn_error_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p)

# --------------------------------------------------------------------------
# Pytest CLI option
# --------------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--grug-lib",
        action="store",
        default=None,
        help="Path to the shared library (tests.so) containing grug_tests_run()",
    )

@pytest.fixture(scope="session")
def grug_lib(request):
    lib_path = request.config.getoption("--grug-lib")
    if not lib_path:
        pytest.exit("Error: You must specify --grug-lib=path/to/tests.so")

    lib_path = Path(lib_path)
    if not lib_path.is_file():
        pytest.exit(f"Error: Shared library not found: {lib_path}")

    lib = ctypes.CDLL(str(lib_path))

    # grug_tests_run signature
    lib.grug_tests_run.argtypes = [
        compile_grug_file_t,
        init_globals_fn_dispatcher_t,
        on_fn_dispatcher_t,
        dump_file_to_json_t,
        generate_file_from_json_t,
        game_fn_error_t,
        ctypes.c_char_p,
    ]
    lib.grug_tests_run.restype = None

    return lib
