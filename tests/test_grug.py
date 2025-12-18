import ctypes
import sys
import traceback
from pathlib import Path
from typing import Any, Optional

import pytest

from grug import Bindings
from grug.backend import GrugValue


class GrugValueWorkaround(ctypes.Structure):
    """
    This defines a Structure of the exact same size and alignment as GrugValue.

    When using `ctypes.Union`, Python's logic for "return by value" is flawed.
    It seemingly assumes complex types (like Unions) are always too large
    for registers and must be returned via memory. It allocates a buffer,
    passes its address to C (which C ignores), and then reads that buffer back.
    Since C never wrote to it, you see garbage memory.

    Quoting a [cpython GitHub issue](https://github.com/python/cpython/issues/60779) from 2012:
    > ctypes pretends to support passing arguments to C functions
    > that are unions (not pointers to unions), but that's a lie.
    > In fact, the underlying libffi does not support it.
    > The attached example misbehaves on Linux x86-64.
    """

    _fields_ = [("_blob", ctypes.c_uint64)]


def test_grug(
    grug_tests_path: Path, whitelisted_test: Optional[str], grug_lib: ctypes.PyDLL
) -> None:
    bindings = Bindings(grug_tests_path / "mod_api.json")

    GameFnRegistrator(bindings, grug_lib).register_game_fns()

    @ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p)
    def compile_grug_file(path: bytes, mod_name: bytes) -> Optional[bytes]:
        msg = bindings.compile_grug_file(path.decode(), mod_name.decode())
        return msg.encode() if msg else None

    @ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    def init_globals_fn_dispatcher(path: bytes) -> None:
        bindings.init_globals_fn_dispatcher(path.decode())

    @ctypes.CFUNCTYPE(
        None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p
    )  # TODO: Change this ctypes.c_void_p to `const union grug_value args[]`
    def on_fn_dispatcher(on_fn_name: bytes, grug_file_path: bytes, args: int) -> None:
        # TODO: Translate `args` from a ctypes.c_void_p to a Python List of GrugValue types
        try:
            bindings.on_fn_dispatcher(
                on_fn_name.decode(), grug_file_path.decode(), args or []
            )
        except Exception:
            traceback.print_exc(file=sys.stderr)

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def dump_file_to_json(input_grug_path: bytes, output_json_path: bytes) -> bool:
        return bindings.dump_file_to_json(
            input_grug_path.decode(), output_json_path.decode()
        )

    @ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p)
    def generate_file_from_json(
        input_json_path: bytes, output_grug_path: bytes
    ) -> bool:
        return bindings.generate_file_from_json(
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
    def __init__(self, bindings: Any, grug_lib: ctypes.PyDLL):
        self.bindings = bindings
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

    def _register_void(self, name: str):
        fn = self._get_fn(name)

        fn.argtypes = (ctypes.POINTER(GrugValue),)
        fn.restype = None

        self._register(name, fn)

    def _register_void_argless(self, name: str):
        fn = self._get_fn(name)

        fn.argtypes = ()
        fn.restype = None

        self._register(name, fn)

    def _register_value(self, name: str):
        fn = self._get_fn(name)

        fn.argtypes = (ctypes.POINTER(GrugValue),)
        fn.restype = GrugValueWorkaround

        self._register(name, fn)

    def _register_value_argless(self, name: str):
        fn = self._get_fn(name)

        fn.argtypes = ()
        fn.restype = GrugValueWorkaround

        self._register(name, fn)

    def _get_fn(self, name: str):
        return self.grug_lib["game_fn_" + name]

    def _register(self, name: str, fn: Any):
        self.bindings.register_game_fn(name, fn)


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":
    pytest.main(sys.argv)
