import ctypes
import sys
import traceback
from pathlib import Path
from typing import List, Optional

import pytest

import grug
from grug.entity import Entity
from grug.grug_file import GrugFile
from grug.grug_state import GrugState
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
    state = grug.init(
        mod_api_path=str(grug_tests_path / "mod_api.json"),
        mods_dir_path=str(grug_tests_path / "tests"),
    )

    GameFnRegistrator(state, grug_lib).register_game_fns()

    grug_file: Optional[GrugFile] = None
    grug_entity: Optional[Entity] = None

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
    def compile_grug_file(path: bytes) -> Optional[bytes]:
        nonlocal grug_file
        try:
            grug_file = state.compile_grug_file(path.decode())
        except Exception as e:
            return str(e).encode()
        return None

    @ctypes.CFUNCTYPE(None)
    def init_globals_fn_dispatcher() -> None:
        nonlocal grug_entity
        try:
            assert grug_file is not None
            state.next_id = 42
            grug_entity = grug_file.create_entity()
        except Exception:
            traceback.print_exc(file=sys.stderr)

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.POINTER(GrugValueUnion))
    def on_fn_dispatcher(c_on_fn_name: bytes, c_args: List[GrugValueUnion]) -> None:
        try:
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
        except Exception:
            traceback.print_exc(file=sys.stderr)

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def dump_file_to_json(input_grug_path: bytes, output_json_path: bytes) -> bool:
        return state.dump_file_to_json(
            input_grug_path.decode(), output_json_path.decode()
        )

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(
        input_json_path: bytes, output_grug_path: bytes
    ) -> bool:
        return state.generate_file_from_json(
            input_json_path.decode(), output_grug_path.decode()
        )

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def game_fn_error(msg: bytes) -> None:
        print(f"game_fn_error called with {msg.decode()}")  # TODO: REMOVE!

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

        c_fn.argtypes = (ctypes.POINTER(GrugValueUnion),)
        c_fn.restype = None

        def fn(*args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            c_fn(c_args)

        self.state.register_game_fn(name, fn)

    def _register_void_argless(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = ()
        c_fn.restype = None

        def fn(*args: GrugValue):
            c_fn()

        self.state.register_game_fn(name, fn)

    def _register_value(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = (ctypes.POINTER(GrugValueUnion),)
        c_fn.restype = GrugValueWorkaround

        return_type = self._get_return_type(name)

        def fn(*args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            result: GrugValueWorkaround = c_fn(*c_args)
            return self._unpack_workaround(result, return_type)

        self.state.register_game_fn(name, fn)

    def _register_value_argless(self, name: str):
        c_fn = self._get_c_fn(name)

        c_fn.argtypes = ()
        c_fn.restype = GrugValueWorkaround

        return_type = self._get_return_type(name)

        def fn(*args: GrugValue):
            result: GrugValueWorkaround = c_fn()
            return self._unpack_workaround(result, return_type)

        self.state.register_game_fn(name, fn)


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":
    pytest.main(sys.argv)
