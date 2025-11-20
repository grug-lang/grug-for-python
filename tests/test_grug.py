import ctypes

import pytest

from grug import Bindings


def test_grug(grug_lib, grug_tests_path):

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
    def compile_grug_file(path):
        msg = Bindings().compile_grug_fn(path.decode())
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
    def dump_file_to_json(input_path, output_path):
        try:
            with open(input_path, "rb") as fsrc, open(output_path, "wb") as fdst:
                fdst.write(fsrc.read())
            return True
        except:
            return False

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(input_path, output_path):
        try:
            with open(input_path, "rb") as fsrc, open(output_path, "wb") as fdst:
                fdst.write(fsrc.read())
            return True
        except:
            return False

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def game_fn_error(msg):
        print(f"game_fn_error called with {msg.decode()}")

    grug_lib.grug_tests_run(
        str(grug_tests_path / "tests").encode(),
        compile_grug_file,
        init_globals_fn_dispatcher,
        on_fn_dispatcher,
        dump_file_to_json,
        generate_file_from_json,
        game_fn_error,
        None,
    )


# Enables stepping through code with VS Code its Python debugger.
# Click the dropdown button next to the play button at the top-right of the file,
# and then click `Python Debugger: Debug Python File`.
if __name__ == "__main__":
    pytest.main(["--grug-tests-path=../grug-tests", "-s", "-v", __file__])
