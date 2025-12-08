import ctypes
import sys

import pytest

from grug import Bindings


def test_grug(grug_tests_path, whitelisted_test, grug_lib):
    bindings = Bindings(grug_tests_path / "mod_api.json")

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p)
    def compile_grug_file(path, mod_name):
        msg = bindings.compile_grug_fn(path.decode(), mod_name.decode())
        return msg.encode() if msg else None

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def init_globals_fn_dispatcher(path):
        print(f"init_globals_fn_dispatcher called with {path.decode()}")

    @ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t
    )  # TODO: Change this ctypes.c_void_p to `struct grug_value values[]`
    def on_fn_dispatcher(fn_name, grug_file_path, values, value_count):
        print(f"on_fn_dispatcher: {fn_name.decode()} {grug_file_path.decode()}")

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def dump_file_to_json(input_grug_path, output_json_path):
        return bindings.dump_file_to_json(
            input_grug_path.decode(), output_json_path.decode()
        )

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(input_json_path, output_grug_path):
        return bindings.generate_file_from_json(
            input_json_path.decode(), output_grug_path.decode()
        )

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def game_fn_error(msg):
        print(f"game_fn_error called with {msg.decode()}")

    print("\n")

    grug_lib.grug_tests_run(
        str(grug_tests_path / "tests").encode(),
        compile_grug_file,
        init_globals_fn_dispatcher,
        on_fn_dispatcher,
        dump_file_to_json,
        generate_file_from_json,
        game_fn_error,
        whitelisted_test.encode() if whitelisted_test else None,
    )


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":
    pytest.main(sys.argv)
