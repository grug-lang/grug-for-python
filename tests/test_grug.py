import ctypes
import sys
import traceback
from pathlib import Path
from typing import List, Optional, Union

import pytest

import grug
from grug.entity import Entity, ReraisedGameFnError, StackOverflow, TimeLimitExceeded
from grug.grug_state import GrugFile, GrugRuntimeErrorType, GrugState
from grug.grug_value import GrugValue


class GrugValueUnion(ctypes.Union):
    _fields_ = [
        ("_number", ctypes.c_double),
        ("_bool", ctypes.c_bool),
        ("_string", ctypes.c_char_p),
        ("_id", ctypes.c_uint64),
    ]


class GrugValueWorkaround(ctypes.Structure):
    """
    This defines a Structure of the exact same size and alignment as GrugValueUnion.

    When using `ctypes.Union`, Python's logic for "return by value" is flawed.
    It seemingly assumes complex types (like Unions) are always too large
    for registers and must be returned via memory. It allocates a buffer,
    passes its address to C (which C ignores), and then reads that buffer back.
    Since C never wrote to it, you see garbage memory.

    Quoting a [cpython GitHub issue](https://github.com/python/cpython/issues/60779) from 2012:
    > ctypes pretends to support passing arguments to C functions
    > that are unions (not pointers to unions), but that's a lie.
    > In fact, the underlying libffi does not support it.
    """

    _fields_ = [("_blob", ctypes.c_uint64)]


# Callback type definitions
create_grug_state_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
)
destroy_grug_state_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
compile_grug_file_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)
)
init_globals_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
call_export_fn_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.POINTER(GrugValueUnion),
    ctypes.c_size_t,
)
dump_file_to_json_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
)
generate_file_from_json_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
)
game_fn_error_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)


class GrugStateVTableStruct(ctypes.Structure):
    """
    Corresponds to struct grug_state_vtable in tests.h
    """

    _fields_ = [
        ("create_grug_state", create_grug_state_t),
        ("destroy_grug_state", destroy_grug_state_t),
        ("compile_grug_file", compile_grug_file_t),
        ("init_globals", init_globals_t),
        ("call_export_fn", call_export_fn_t),
        ("dump_file_to_json", dump_file_to_json_t),
        ("generate_file_from_json", generate_file_from_json_t),
        ("game_fn_error", game_fn_error_t),
    ]


_g_grug_lib: ctypes.PyDLL

_grug_runtime_err: Optional[
    Union[TimeLimitExceeded, StackOverflow, ReraisedGameFnError]
] = None


def custom_runtime_error_handler(
    reason: str,
    grug_runtime_error_type: GrugRuntimeErrorType,
    on_fn_name: str,
    on_fn_path: str,
):
    _g_grug_lib.grug_tests_runtime_error_handler(
        reason.encode(),
        grug_runtime_error_type.value,
        on_fn_name.encode(),
        on_fn_path.encode(),
    )


def c_to_py_value(value: GrugValueUnion, typ: str):
    if typ == "number":
        return float(value._number)
    if typ == "bool":
        return bool(value._bool)
    if typ == "string":
        return ctypes.string_at(value._string).decode()
    return int(value._id)


def test_grug(
    grug_tests_path: Path, whitelisted_test: Optional[str], grug_lib: ctypes.PyDLL
) -> None:
    global _g_grug_lib
    _g_grug_lib = grug_lib

    state: Optional[GrugState] = None

    id_map: dict[int, GrugFile] = {}
    path_map: dict[str, int] = {}

    current_entity: Optional[Entity] = None

    @ctypes.CFUNCTYPE(
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_char_p),
    )
    def compile_grug_file(
        state_ptr: int,
        path: bytes,
        out_err: ctypes.POINTER(ctypes.c_char_p), # type: ignore
    ) -> int:
        nonlocal id_map
        nonlocal path_map
        try:
            assert state
            path_str = path.decode()
            grug_file = state.compile_grug_file(path_str)

            if path_str in path_map:
                file_id = path_map[path_str]
                id_map[file_id] = grug_file
            else:
                file_id = len(path_map) + 1
                path_map[path_str] = file_id
                # sanity check
                assert file_id not in id_map
                id_map[file_id] = grug_file
            return file_id
        except Exception as e:
            out_err[0] = str(e).encode()
            return -1

    @ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
    def init_globals(state_ptr: int, file_id: int) -> None:
        nonlocal id_map
        nonlocal current_entity
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            assert state
            state.next_id = 42
            grug_file = id_map[file_id]
            assert grug_file

            current_entity = grug_file.create_entity()
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            # Necessary, as propagating exceptions from
            # this CFUNCTYPE function doesn't work.
            _grug_runtime_err = e
        except Exception:
            traceback.print_exc(file=sys.stderr)
        

    @ctypes.CFUNCTYPE(
        None,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(GrugValueUnion),
        ctypes.c_size_t,
    )
    def call_export_fn(
        state_ptr: int,
        file_id: int,
        c_on_fn_name: bytes,
        c_args: List[GrugValueUnion],
        args_len: int,
    ) -> None:
        nonlocal id_map
        nonlocal state
        nonlocal current_entity
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            on_fn_name: str = c_on_fn_name.decode()

            grug_file = id_map[file_id]
            assert grug_file
            assert current_entity
            on_fn_decl = grug_file.on_fns.get(on_fn_name)
            if not on_fn_decl:
                raise RuntimeError(
                    f"The function '{on_fn_name}' is not defined by the file {grug_file.relative_path}"
                )

            assert len(on_fn_decl.arguments) == args_len
            args = [
                c_to_py_value(arg, argument.type_name)
                for arg, argument in zip(c_args or [], on_fn_decl.arguments)
            ]

            assert current_entity is not None
            on_fn = getattr(current_entity, on_fn_name)
            on_fn(*args)
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            # Necessary, as propagating exceptions from
            # this CFUNCTYPE function doesn't work.
            _grug_runtime_err = e
        except Exception:
            traceback.print_exc(file=sys.stderr)

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p)
    def dump_file_to_json(
        state_ptr: int, input_grug_path: bytes, output_json_path: bytes
    ) -> bool:
        assert state
        return state.dump_file_to_json(
            input_grug_path.decode(), output_json_path.decode()
        )

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(
        state_ptr: int, input_json_path: bytes, output_grug_path: bytes
    ) -> bool:
        assert state
        return state.generate_file_from_json(
            input_json_path.decode(), output_grug_path.decode()
        )

    _original_run_game_fn = Entity._run_game_fn  # pyright: ignore[reportPrivateUsage]

    _game_fn_error_reason: Optional[str] = None

    def _test_run_game_fn(
        self: Entity, name: str, *args: GrugValue
    ) -> Optional[GrugValue]:
        nonlocal _game_fn_error_reason

        # Call the original method
        result = _original_run_game_fn(self, name, *args)

        # Raise _game_fn_error_reason if it's not None
        if _game_fn_error_reason is not None:
            reason = _game_fn_error_reason
            assert state
            self.state.runtime_error_handler(
                reason,
                GrugRuntimeErrorType.GAME_FN_ERROR,
                self.fn_name,
                self.file.relative_path,
            )

            _game_fn_error_reason = None
            raise ReraisedGameFnError(reason)

        return result

    # Patch the method for testing
    Entity._run_game_fn = _test_run_game_fn  # pyright: ignore[reportPrivateUsage]

    @ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)
    def game_fn_error(state_ptr: int, reason: bytes) -> None:
        nonlocal _game_fn_error_reason
        _game_fn_error_reason = ctypes.string_at(reason).decode()

    @ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p)
    def create_grug_state(tests_path: bytes, mod_api_path: bytes) -> int:
        nonlocal state
        state = grug.init(
            runtime_error_handler=custom_runtime_error_handler,
            mod_api_path=ctypes.string_at(tests_path).decode(),
            mods_dir_path=ctypes.string_at(mod_api_path).decode(),
        )
        state.next_id = 42
        GameFnRegistrator(state, grug_lib).register_game_fns()
        return 0

    @ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    def destroy_grug_state(state_ptr: int):
        nonlocal state
        assert state
        state = None

    print("\n")

    grug_state_vtable: GrugStateVTableStruct = GrugStateVTableStruct(
        create_grug_state,
        destroy_grug_state,
        compile_grug_file,
        init_globals,
        call_export_fn,
        dump_file_to_json,
        generate_file_from_json,
        game_fn_error,
    )

    grug_lib.grug_tests_run(
        str(grug_tests_path / "tests").encode(),
        str(grug_tests_path / "mod_api.json").encode(),
        grug_state_vtable,
        whitelisted_test.encode() if whitelisted_test else None,
    )


class GameFnRegistrator:
    def __init__(self, state: GrugState, grug_lib: ctypes.PyDLL):
        self.state = state
        self.grug_lib = grug_lib

    def register_game_fns(self):
        for name in (
            "nothing",
            "magic",
            "initialize",
            "initialize_bool",
            "identity",
            "max",
            "say",
            "sin",
            "cos",
            "mega",
            "get_false",
            "set_is_happy",
            "mega_f32",
            "mega_i32",
            "draw",
            "blocked_alrm",
            "spawn",
            "has_resource",
            "has_entity",
            "has_string",
            "get_opponent",
            "get_os",
            "set_d",
            "set_opponent",
            "motherload",
            "motherload_subless",
            "offset_32_bit_f32",
            "offset_32_bit_i32",
            "offset_32_bit_string",
            "talk",
            "get_position",
            "set_position",
            "cause_game_fn_error",
            "call_on_b_fn",
            "store",
            "retrieve",
            "box_number",
        ):
            self._register_fn(name)

    def _get_c_args(self, *args: GrugValue):
        c_args = (GrugValueUnion * len(args))()
        keepalive: List[bytes] = []

        for i, v in enumerate(args):
            if isinstance(v, float):
                c_args[i]._number = v
            elif isinstance(v, bool):
                c_args[i]._bool = v
            elif isinstance(v, str):
                b = v.encode()
                keepalive.append(b)
                c_args[i]._string = ctypes.c_char_p(b)
            else:
                assert isinstance(v, int)
                c_args[i]._id = ctypes.c_uint64(v)

        return c_args, keepalive

    def _unpack_workaround(
        self, c_workaround: GrugValueWorkaround, return_type: str
    ) -> GrugValue:
        """
        Creates a GrugValueUnion, and copies the bits from GrugValueWorkaround into it.
        See the GrugValueWorkaround class docs for more information.
        """
        value = GrugValueUnion()
        ctypes.memmove(
            ctypes.byref(value), ctypes.byref(c_workaround), ctypes.sizeof(value)
        )
        return c_to_py_value(value, return_type)

    def _register_fn(self, name: str):
        c_fn = self.grug_lib["game_fn_" + name]

        c_fn.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(GrugValueUnion),
        )
        c_fn.restype = GrugValueWorkaround

        return_type = self.state.mod_api["game_functions"][name].get("return_type")

        def fn(state: GrugState, *args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            result: GrugValueWorkaround = c_fn(0, c_args)
            if _grug_runtime_err is not None:
                raise _grug_runtime_err
            return self._unpack_workaround(result, return_type)

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":
    pytest.main(sys.argv)
