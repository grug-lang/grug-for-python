import ctypes
from pathlib import Path
from typing import Optional, cast

import pytest

# Callback type definitions
compile_grug_file_t = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
init_globals_fn_dispatcher_t = ctypes.CFUNCTYPE(None)
on_fn_dispatcher_t = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_void_p
)  # TODO: Change this ctypes.c_void_p to `const union grug_value args[]`
dump_file_to_json_t = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
generate_file_from_json_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p
)
game_fn_error_t = ctypes.CFUNCTYPE(None, ctypes.c_char_p)


def pytest_addoption(parser: pytest.Parser) -> None:
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
def grug_tests_path(request: pytest.FixtureRequest) -> Path:
    """
    Returns the path to the grug-tests repository.
    """
    path = cast(Optional[str], request.config.getoption("--grug-tests-path"))
    if not path:
        pytest.exit("Error: You must specify --grug-tests-path=path/to/grug-tests")

    path_obj = Path(path)
    if not path_obj.is_dir():
        pytest.exit(f"Error: Directory not found: {path_obj}")

    return path_obj


@pytest.fixture(scope="session")
def whitelisted_test(request: pytest.FixtureRequest) -> Optional[str]:
    """
    Returns the name of a whitelisted test.
    """
    return cast(Optional[str], request.config.getoption("--whitelisted-test"))


@pytest.fixture(scope="session")
def grug_lib(grug_tests_path: Path) -> ctypes.PyDLL:
    """
    Loads tests.so and sets argument signatures.
    """
    lib_path = grug_tests_path / "build/libtests.so"
    if not lib_path.is_file():
        pytest.exit(f"Error: Shared library not found: {lib_path}")

    lib = ctypes.PyDLL(str(lib_path))

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
