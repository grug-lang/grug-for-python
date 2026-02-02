import ctypes
import sys
import traceback
from pathlib import Path
from typing import List, Optional, Union

import pytest

import grug
from grug.entity import Entity, ReraisedGameFnError, StackOverflow, TimeLimitExceeded
from grug.grug_state import GrugRuntimeErrorType, GrugState, GrugFile
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

    state = None

    grug_file: Optional[GrugFile] = None
    grug_entity: Optional[Entity] = None

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p)
    def compile_grug_file(state_int: int, path: bytes) -> Optional[bytes]:
        nonlocal grug_file
        try:
            grug_file = state.compile_grug_file(path.decode())
        except Exception as e:
            return str(e).encode()
        return None

    @ctypes.CFUNCTYPE(None, ctypes.c_size_t)
    def init_globals_fn_dispatcher(state_int: int) -> None:
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            state.next_id = 42

            nonlocal grug_entity
            assert grug_file is not None
            grug_entity = grug_file.create_entity()
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            # Necessary, as propagating exceptions from
            # this CFUNCTYPE function doesn't work.
            _grug_runtime_err = e
        except Exception:
            traceback.print_exc(file=sys.stderr)

    on_fn_name: Optional[str] = None

    @ctypes.CFUNCTYPE(None, ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(GrugValueUnion))
    def on_fn_dispatcher(state_int: int, c_on_fn_name: bytes, c_args: List[GrugValueUnion]) -> None:
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            nonlocal on_fn_name
            on_fn_name = c_on_fn_name.decode()

            assert grug_file
            on_fn_decl = grug_file.on_fns.get(on_fn_name)
            if not on_fn_decl:
                raise RuntimeError(
                    f"The function '{on_fn_name}' is not defined by the file {grug_file.relative_path}"
                )

            args = [
                c_to_py_value(arg, argument.type_name)
                for arg, argument in zip(c_args or [], on_fn_decl.arguments)
            ]

            assert grug_entity is not None
            on_fn = getattr(grug_entity, on_fn_name)
            on_fn(*args)
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            # Necessary, as propagating exceptions from
            # this CFUNCTYPE function doesn't work.
            _grug_runtime_err = e
        except Exception:
            traceback.print_exc(file=sys.stderr)

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p)
    def dump_file_to_json(state_int: int, input_grug_path: bytes, output_json_path: bytes) -> bool:
        return state.dump_file_to_json(
            input_grug_path.decode(), output_json_path.decode()
        )

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(
        state_int: int, input_json_path: bytes, output_grug_path: bytes
    ) -> bool:
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

    @ctypes.CFUNCTYPE(None, ctypes.c_size_t, ctypes.c_char_p)
    def game_fn_error(state_int: int, reason: bytes) -> None:
        nonlocal _game_fn_error_reason
        _game_fn_error_reason = ctypes.string_at(reason).decode()

    @ctypes.CFUNCTYPE(ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p)
    def create_grug_state(tests_path: bytes, mod_api_path: bytes) -> int:
        nonlocal state
        state = grug.init(
            runtime_error_handler=custom_runtime_error_handler,
            mod_api_path=ctypes.string_at(tests_path).decode(),
            mods_dir_path=ctypes.string_at(mod_api_path).decode()
        )
        GameFnRegistrator(state, grug_lib).register_game_fns()

        return 0

    @ctypes.CFUNCTYPE(None, ctypes.c_size_t)
    def destroy_grug_state(state_int: int):
        nonlocal state
        state = None

    print("\n")

    grug_lib.grug_tests_run(
        str(grug_tests_path / "tests").encode(),
        str(grug_tests_path / "mod_api.json").encode(),
        create_grug_state,
        destroy_grug_state,
        compile_grug_file,
        init_globals_fn_dispatcher,
        on_fn_dispatcher,
        dump_file_to_json,
        generate_file_from_json,
        game_fn_error,
        whitelisted_test.encode() if whitelisted_test else None,
    )


class GameFnRegistrator:
    def __init__(self, state: GrugState, grug_lib: ctypes.PyDLL):
        self.state = state
        self.grug_lib = grug_lib

    def register_game_fns(self):
        self._register_void_argless("nothing")
        self._register_value_argless("magic")
        self._register_void("initialize")
        self._register_void("initialize_bool")
        self._register_value("identity")
        self._register_value("max")
        self._register_void("say")
        self._register_value("sin")
        self._register_value("cos")
        self._register_void("mega")
        self._register_value_argless("get_false")
        self._register_void("set_is_happy")
        self._register_void("mega_f32")
        self._register_void("mega_i32")
        self._register_void("draw")
        self._register_void_argless("blocked_alrm")
        self._register_void("spawn")
        self._register_value("has_resource")
        self._register_value("has_entity")
        self._register_value("has_string")
        self._register_value_argless("get_opponent")
        self._register_value_argless("get_os")
        self._register_void("set_d")
        self._register_void("set_opponent")
        self._register_void("motherload")
        self._register_void("motherload_subless")
        self._register_void("offset_32_bit_f32")
        self._register_void("offset_32_bit_i32")
        self._register_void("offset_32_bit_string")
        self._register_void("talk")
        self._register_value("get_position")
        self._register_void("set_position")
        self._register_void_argless("cause_game_fn_error")
        self._register_void_argless("call_on_b_fn")
        self._register_void("store")
        self._register_value_argless("retrieve")
        self._register_value("box_number")

    def _get_c_fn(self, name: str):
        return self.grug_lib["game_fn_" + name]

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

    def _get_return_type(self, name: str):
        return self.state.mod_api["game_functions"][name].get("return_type")

    def _register_void(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = (ctypes.c_size_t, ctypes.POINTER(GrugValueUnion),)
        c_fn.restype = None

        def fn(state: GrugState, *args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            c_fn(0, c_args)
            if _grug_runtime_err is not None:
                raise _grug_runtime_err

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]

    def _register_void_argless(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = (ctypes.c_size_t, )
        c_fn.restype = None

        def fn(state: GrugState ,*args: GrugValue):
            c_fn(0)
            if _grug_runtime_err is not None:
                raise _grug_runtime_err

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]

    def _register_value(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = (ctypes.c_size_t, ctypes.POINTER(GrugValueUnion),)
        c_fn.restype = GrugValueWorkaround

        return_type = self._get_return_type(name)

        def fn(state: GrugState ,*args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            result: GrugValueWorkaround = c_fn(0, *c_args)
            if _grug_runtime_err is not None:
                raise _grug_runtime_err
            return self._unpack_workaround(result, return_type)

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]

    def _register_value_argless(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = (ctypes.c_size_t, )
        c_fn.restype = GrugValueWorkaround

        return_type = self._get_return_type(name)

        def fn(state_int: int ,*args: GrugValue):
            result: GrugValueWorkaround = c_fn(0)
            if _grug_runtime_err is not None:
                raise _grug_runtime_err
            return self._unpack_workaround(result, return_type)

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":
    pytest.main(sys.argv)
