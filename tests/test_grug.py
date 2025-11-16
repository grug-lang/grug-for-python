import ctypes

def test_grug(grug_lib, grug_tests_path):

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
    def compile_grug_file(path):
        # TODO: Call the frontend here, since it is responsible for detecting compilation errors

        if b'err/assignment_isnt_expression' in path:
            return b'Expected token type OPEN_BRACE_TOKEN, but got ASSIGNMENT_TOKEN on line 4'
        elif b'err/bool_cant_be_initialized_with_1' in path:
            return b'haha'

        return None

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def init_globals_fn_dispatcher(path):
        print(f"init_globals_fn_dispatcher called with {path.decode()}")

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t) # TODO: Change this ctypes.c_void_p to `struct grug_value values[]`
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
        str(grug_tests_path / "tests").encode("utf-8"),
        compile_grug_file,
        init_globals_fn_dispatcher,
        on_fn_dispatcher,
        dump_file_to_json,
        generate_file_from_json,
        game_fn_error,
        None
    )
