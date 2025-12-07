import ctypes
from pathlib import Path

import pytest

# Callback type definitions
compile_grug_file_t = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
init_globals_fn_dispatcher_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
on_fn_dispatcher_t = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t
)  # TODO: Change this ctypes.c_void_p to `struct grug_value values[]`
dump_file_to_json_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
generate_file_from_json_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p
)
game_fn_error_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p)


def pytest_addoption(parser):
    parser.addoption(
        "--grug-tests-path",
        action="store",
        default=None,
        required=True,
        help="Path to the grug-tests repository",
    )
    parser.addoption(
        "--whitelisted-test",
        action="store",
        default=None,
        required=False,
        help="A specific test name to run",
    )


@pytest.fixture(scope="session")
def grug_tests_path(request):
    """
    Returns the path to the grug-tests repository.
    """
    path = request.config.getoption("--grug-tests-path")
    if not path:
        pytest.exit("Error: You must specify --grug-tests-path=path/to/grug-tests")

    path = Path(path)
    if not path.is_dir():
        pytest.exit(f"Error: Directory not found: {path}")

    return path


@pytest.fixture(scope="session")
def whitelisted_test(request):
    """
    Returns the name of a whitelisted test.
    """
    return request.config.getoption("--whitelisted-test")


@pytest.fixture(scope="session")
def grug_lib(grug_tests_path):
    """
    Loads tests.so and sets argument signatures.
    """
    lib_path = grug_tests_path / "tests.so"
    if not lib_path.is_file():
        pytest.exit(f"Error: Shared library not found: {lib_path}")

    lib = ctypes.CDLL(str(lib_path))

    # Correct signature of grug_tests_run
    lib.grug_tests_run.argtypes = [
        ctypes.c_char_p,
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
