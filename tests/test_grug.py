import ctypes
import sys
import traceback
from pathlib import Path
from enum import IntEnum
from typing import List, Optional, Tuple, Union

import pytest  # pyright: ignore[reportMissingImports]

import grug
from grug.entity import Entity, ReraisedGameFnError, StackOverflow, TimeLimitExceeded
from grug.grug_state import GrugFile, GrugRuntimeErrorType, GrugState
from grug.types import (
    GrugValue,
    HostFn,
    ExistentialType,
    IdType,
    PrimitiveType,
    Type,
)
from grug.mod_api import get_mod_api


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


class CGrugType(ctypes.Structure):
    pass


class CGrugTypeIdData(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("generics", ctypes.POINTER(CGrugType)),
        ("generics_len", ctypes.c_size_t),
    ]


class CGrugTypeData(ctypes.Union):
    _fields_ = [
        ("id", CGrugTypeIdData),
        ("resource_extension", ctypes.c_char_p),
        ("entity_type", ctypes.c_char_p),
    ]


CGrugType._fields_ = [
    ("type", ctypes.c_uint32),
    ("data", CGrugTypeData),
]

class GrugType(IntEnum):
    VOID = 0
    BOOL = 1
    NUMBER = 2
    STRING = 3
    ID = 4
    RESOURCE = 5
    ENTITY = 6


game_fn_c_t = ctypes.CFUNCTYPE(
    GrugValueWorkaround, ctypes.c_void_p, ctypes.POINTER(GrugValueUnion)
)
generic_fn_reg_c_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.POINTER(CGrugType)
)


def c_to_py_value(value: GrugValueUnion, typ: Type):
    if typ == PrimitiveType.VOID:
        return None
    if typ == PrimitiveType.NUMBER:
        return float(value._number)
    if typ == PrimitiveType.BOOL:
        return bool(value._bool)
    if typ == PrimitiveType.STRING:
        return ctypes.string_at(value._string).decode()
    return int(value._id)


def substitute_type(typ: Type, generics: List[Type]) -> Type:
    if isinstance(typ, ExistentialType):
        return generics[typ.idx]
    if isinstance(typ, IdType):
        return IdType(typ.name, [substitute_type(generic, generics) for generic in typ.generics])
    return typ


def py_type_to_c_type(typ: Type) -> Tuple[CGrugType, List[object]]:
    keepalive: List[object] = []
    c_type = CGrugType()

    # Can never pass void, resource, entity, or an existential to a host function
    assert(typ != PrimitiveType.VOID)
    if typ == PrimitiveType.BOOL:
        c_type.type = GrugType.BOOL
    elif typ == PrimitiveType.NUMBER:
        c_type.type = GrugType.NUMBER
    elif typ == PrimitiveType.STRING:
        c_type.type = GrugType.STRING
    # else type is IdType
    else:
        assert(isinstance(typ, IdType))
        c_type.type = GrugType.ID
        name = typ.name.encode()
        keepalive.append(name)
        c_type.data.id.name = name

        c_generics: List[CGrugType] = []
        for generic in typ.generics:
            c_generic, generic_keepalive = py_type_to_c_type(generic)
            c_generics.append(c_generic)
            keepalive.extend(generic_keepalive)

        generic_array = (CGrugType * len(c_generics))(*c_generics)
        keepalive.append(generic_array)
        c_type.data.id.generics = generic_array
        c_type.data.id.generics_len = len(c_generics)

    return c_type, keepalive


# Callback type definitions
parse_mod_api_t = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_char_p)
create_grug_state_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool
)
destroy_grug_state_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
compile_grug_file_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)
)
destroy_grug_file_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
create_entity_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)
)
destroy_entity_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
update_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p))
call_export_fn_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.POINTER(GrugValueUnion),
    ctypes.c_size_t,
)
grug_to_json_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t
)
json_to_grug_t = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t
)
game_fn_error_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_char_p)


class GrugStateVTableStruct(ctypes.Structure):
    """
    Corresponds to struct grug_state_vtable in tests.h
    """

    _fields_ = [
        ("parse_mod_api", parse_mod_api_t),
        ("create_grug_state", create_grug_state_t),
        ("destroy_grug_state", destroy_grug_state_t),
        ("compile_grug_file", compile_grug_file_t),
        ("destroy_grug_file", destroy_grug_file_t),
        ("create_entity", create_entity_t),
        ("destroy_entity", destroy_entity_t),
        ("update", update_t),
        ("call_export_fn", call_export_fn_t),
        ("grug_to_json", grug_to_json_t),
        ("json_to_grug", json_to_grug_t),
        ("game_fn_error", game_fn_error_t),
    ]


_g_grug_lib: ctypes.CDLL

_grug_runtime_err: Optional[
    Union[TimeLimitExceeded, StackOverflow, ReraisedGameFnError]
] = None

_game_fn_error_reason: Optional[str] = None


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


def test_grug(
    grug_tests_path: Path, whitelisted_test: Optional[str], grug_lib: ctypes.CDLL
) -> None:
    global _g_grug_lib
    _g_grug_lib = grug_lib

    states: dict[int, GrugState] = {}
    files: dict[int, GrugFile] = {}
    entities: dict[int, Entity] = {}

    error_buffers: List[bytes] = []

    @parse_mod_api_t
    def parse_mod_api(
        path: bytes,
    ) -> Union[bytes, None]:
        try:
            path_str = path.decode()
            get_mod_api(Path(path_str))
            return None
        except Exception as e:
            buf = str(e).encode()
            # This ensures the buffer returned from this function isn't
            # cleaned up before the C code has a chance to use it.
            error_buffers.append(buf)
            return buf

    @compile_grug_file_t
    def compile_grug_file(
        state_ptr: int,
        path: bytes,
        out_err: ctypes.POINTER(ctypes.c_char_p),  # type: ignore
    ) -> int:
        try:
            state = states[state_ptr]

            path_str = path.decode()

            if path_str == "code_reloading/input-D.grug":
                state._update()  # pyright: ignore[reportPrivateUsage]
                file = state.mods["code_reloading"]["input-D.grug"]
                assert isinstance(file, GrugFile)
            else:
                file = state._compile_grug_file(path_str)  # type: ignore

            file_id = len(files) + 1
            files[file_id] = file
            out_err[0] = None
            return file_id
        except Exception as e:
            buf = str(e).encode()
            # This ensures the buffer returned from this function isn't
            # cleaned up before the C code has a chance to use it.
            error_buffers.append(buf)
            out_err[0] = buf
            return -1

    @destroy_grug_file_t
    def destroy_grug_file(state_ptr: int, file_id: int):
        # Clear any lingering runtime errors that hold tracebacks to local entities
        global _grug_runtime_err
        _grug_runtime_err = None

        del files[file_id]

    @create_entity_t
    def create_entity(
        state_ptr: int,
        file_id: int,
        out_err: ctypes.POINTER(ctypes.c_char_p),  # type: ignore
    ) -> int:
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            state = states[state_ptr]
            state.next_id = 42

            file = files[file_id]

            entity = file.create_entity()

            entity_id = len(entities) + 1
            entities[entity_id] = entity
            out_err[0] = None
            return entity_id
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            out_err[0] = str(e).encode()

            # Necessary, as C doesn't propagate exceptions.
            _grug_runtime_err = e

            return -1
        except Exception as e:  # pragma: no cover
            traceback.print_exc(file=sys.stderr)
            return -1

    @destroy_entity_t
    def destroy_entity(state_ptr: int, entity_id: int):
        del entities[entity_id]

    @update_t
    def update(
        state_ptr: int,
        out_err: ctypes.POINTER(ctypes.c_char_p),  # type: ignore
    ) -> None:
        try:
            state = states[state_ptr]
            state._update()  # pyright: ignore[reportPrivateUsage]

            file = state.mods["code_reloading"]["input-D.grug"]
            assert isinstance(file, GrugFile)

            # We have to manually overwrite the old file in the files list,
            # purely because test_grug.py tries to emulate the grug implementation.
            last_file_id = list(files.keys())[-1]
            files[last_file_id] = file

            out_err[0] = None
        except Exception as e:  # pragma: no cover
            out_err[0] = str(e).encode()

    @call_export_fn_t
    def call_export_fn(
        state_ptr: int,
        entity_id: int,
        c_on_fn_name: bytes,
        c_args: List[GrugValueUnion],
        args_len: int,
    ) -> None:
        try:
            global _grug_runtime_err
            _grug_runtime_err = None

            on_fn_name: str = c_on_fn_name.decode()

            entity = entities[entity_id]

            file = entity.file

            on_fn_decl = file.on_fns[on_fn_name]

            assert len(on_fn_decl.parameters) == args_len
            args = [
                c_to_py_value(arg, param.type)
                for arg, param in zip(c_args or [], on_fn_decl.parameters)
            ]

            entity._run_on_fn(on_fn_name, *args)  # pyright: ignore[reportPrivateUsage]
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError) as e:
            # Necessary, as C doesn't propagate exceptions.
            _grug_runtime_err = e
        except Exception:  # pragma: no cover
            traceback.print_exc(file=sys.stderr)

    @grug_to_json_t
    def grug_to_json(
        state_ptr: int,
        input_grug_buffer: bytes,
        output_json_buffer: int,
        output_buffer_len: int,
    ) -> bool:
        try:
            input_text = input_grug_buffer.decode()

            state = states[state_ptr]
            output_text = state.grug_to_json(input_text)

            output_bytes = output_text.encode()
            required_len = len(output_bytes) + 1  # null terminator

            if required_len > output_buffer_len:  # pragma: no cover
                print(
                    f"grug_to_json: output buffer too small "
                    f"(need {required_len} bytes, have {output_buffer_len})",
                    file=sys.stderr,
                )
                return True

            # Treat buffer as writable char array
            buf = (ctypes.c_char * output_buffer_len).from_address(output_json_buffer)

            buf[: len(output_bytes)] = output_bytes
            buf[len(output_bytes)] = b"\0"

            return False

        except Exception:  # pragma: no cover
            traceback.print_exc(file=sys.stderr)
            return True

    @json_to_grug_t
    def json_to_grug(
        state_ptr: int,
        input_json_buffer: bytes,
        output_grug_buffer: int,
        output_buffer_len: int,
    ) -> bool:
        try:
            input_text = input_json_buffer.decode()

            state = states[state_ptr]
            output_text = state.json_to_grug(input_text)

            output_bytes = output_text.encode()
            required_len = len(output_bytes) + 1  # null terminator

            if required_len > output_buffer_len:  # pragma: no cover
                print(
                    f"json_to_grug: output buffer too small "
                    f"(need {required_len} bytes, have {output_buffer_len})",
                    file=sys.stderr,
                )
                return True

            # Treat buffer as writable char array
            buf = (ctypes.c_char * output_buffer_len).from_address(output_grug_buffer)

            buf[: len(output_bytes)] = output_bytes
            buf[len(output_bytes)] = b"\0"

            return False

        except Exception:  # pragma: no cover
            traceback.print_exc(file=sys.stderr)
            return True

    @game_fn_error_t
    def game_fn_error(state_ptr: int, reason: bytes) -> None:
        global _game_fn_error_reason
        _game_fn_error_reason = ctypes.string_at(reason).decode()

    @create_grug_state_t
    def create_grug_state(
        tests_path: bytes, mod_api_path: bytes, unsafe_mode: bool
    ) -> int:
        try:
            state = grug.init(
                runtime_error_handler=custom_runtime_error_handler,
                mod_api_path=ctypes.string_at(tests_path).decode(),
                mods_dir_path=ctypes.string_at(mod_api_path).decode(),
                on_fn_time_limit_ms=100,
            )
        except RuntimeError: # pragma: no cover
            traceback.print_exc(file=sys.stderr)
            return 0
        except Exception:  # pragma: no cover
            traceback.print_exc(file=sys.stderr)
            return 0

        GameFnRegistrator(state, grug_lib).register_game_fns()

        state_id = len(states) + 1
        states[state_id] = state
        return state_id

    @ctypes.CFUNCTYPE(None, ctypes.c_void_p)
    def destroy_grug_state(state_ptr: int):
        del states[state_ptr]

    print("\n")

    grug_state_vtable: GrugStateVTableStruct = GrugStateVTableStruct(
        parse_mod_api,
        create_grug_state,
        destroy_grug_state,
        compile_grug_file,
        destroy_grug_file,
        create_entity,
        destroy_entity,
        update,
        call_export_fn,
        grug_to_json,
        json_to_grug,
        game_fn_error,
    )

    grug_lib.grug_tests_run(
        str(grug_tests_path / "tests").encode(),
        str(grug_tests_path / "mod_api.json").encode(),
        grug_state_vtable,
        whitelisted_test.encode() if whitelisted_test else None,
    )

    assert len(states) == 0
    assert len(files) == 0
    assert len(entities) == 0


class GameFnRegistrator:
    def __init__(self, state: GrugState, grug_lib: ctypes.CDLL):
        self.state = state
        self.grug_lib = grug_lib
        
        self._keepalive: List[bytes] = []

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
            "utils",
            "assert_state_is_not_null",
            "blocked_alrm",
            "spawn",
            "spawn_d",
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
            "print_csv",
            "talk",
            "get_position",
            "set_position",
            "cause_game_fn_error",
            "call_on_b_fn",
            "call_on_b_fn_number",
            "store",
            "retrieve",
            "box_number",
            "vec_number_new",
        ):
            self._register_fn(name)

        for name, native_name in (
            ("vec", "vec_new"),
            ("box", "box"),
            ("default", "default"),
            ("dict", "dict"),
            ("dict_from_vec", "dict_from_vec"),
            ("make_pair", "make_pair"),
            ("cause_game_fn_error_generic", "cause_game_fn_error_generic"),
        ):
            self._register_generic_fn(name, native_name)

        for method_name, native_name in (
            ("push", "vec_number_push"),
            ("pop", "vec_number_pop"),
            ("insert", "vec_number_insert"),
        ):
            self._register_method("VecNumber", method_name, native_name)

        for method_name, native_name in (
            ("assert_state_is_not_null", "Utils_assert_state_is_not_null"),
            ("cause_game_fn_error", "Utils_cause_game_fn_error"),
            ("call_on_b_fn", "Utils_call_on_b_fn"),
        ):
            self._register_method("Utils", method_name, native_name)
        self._register_generic_method("Utils", "cause_game_fn_error_generic", "Utils_cause_game_fn_error_generic")

        for method_name, native_name in (
            ("push", "vec_push"),
            ("pop", "vec_pop"),
            ("insert", "vec_insert"),
        ):
            self._register_generic_method("Vec", method_name, native_name)

        for method_name, native_name in (
            ("get", "box_get"),
            ("set", "box_set"),
        ):
            self._register_generic_method("Box", method_name, native_name)

        self._register_generic_method("Dict", "put", "dict_put")

        self._register_generic_method("Pair", "first", "pair_first")
        self._register_generic_method("Pair", "second", "pair_second")

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
        self, c_workaround: GrugValueWorkaround, return_type: Type
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
    
    def _raise_game_fn_error_if_needed(self, state: GrugState):
        global _game_fn_error_reason

        if _game_fn_error_reason is None:
            return

        reason = _game_fn_error_reason
        _game_fn_error_reason = None

        assert state.executed_file
        assert state.executed_entity

        state.runtime_error_handler(
            reason,
            GrugRuntimeErrorType.GAME_FN_ERROR,
            state.executed_entity.fn_name,
            state.executed_file.relative_path,
        )

        raise ReraisedGameFnError(reason)

    # type of c_fn cannot be expressed properly
    def wrap_fn(self, return_type: Type, c_fn) -> HostFn: # pyright: ignore
        def fn(state: GrugState, *args: GrugValue):
            c_args, _keepalive = self._get_c_args(*args)
            self._keepalive += _keepalive

            # We pass 42 since `state` is a Python object
            # grug-tests just doesn't want us to *accidentally* pass NULL

            # type of c_fn cannot be expressed properly, so it's return type
            # is also unknown
            result: GrugValueWorkaround = c_fn(42, c_args) # pyright: ignore

            self._raise_game_fn_error_if_needed(state)

            if _grug_runtime_err is not None:
                raise _grug_runtime_err

            return self._unpack_workaround(result, return_type) # pyright: ignore
        return fn

    def _register_fn(self, name: str):
        c_fn = self.grug_lib["game_fn_" + name]

        c_fn.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(GrugValueUnion),
        )
        c_fn.restype = GrugValueWorkaround

        return_type = self.state.mod_api.host_fns[name].return_type

        self.state.mod_api.register_fn(None, name, self.wrap_fn(return_type, c_fn)) # pyright: ignore

    def _register_generic_fn(self, name: str, native_name: str):
        c_reg_fn = self.grug_lib["reg_game_fn_" + native_name]
        c_reg_fn.argtypes = (ctypes.POINTER(CGrugType),)
        c_reg_fn.restype = ctypes.c_void_p

        host_fn_data = self.state.mod_api.host_fns[name]

        def register(generics: List[Type]):
            c_generics: List[CGrugType] = []
            keepalive: List[object] = []
            for generic in generics:
                c_generic, generic_keepalive = py_type_to_c_type(generic)
                c_generics.append(c_generic)
                keepalive.extend(generic_keepalive)

            generic_array = (CGrugType * len(c_generics))(*c_generics)
            keepalive.append(generic_array)

            c_fn_ptr = c_reg_fn(generic_array)
            if c_fn_ptr is None:
                return None

            c_fn = game_fn_c_t(c_fn_ptr)
            return_type = substitute_type(host_fn_data.return_type, generics)

            return self.wrap_fn(return_type, c_fn) # pyright: ignore

        self.state.mod_api.register_generic_fn(None, name, register)

    def _register_method(self, class_name: str, name: str, native_name: str):
        c_fn = self.grug_lib["game_fn_" + native_name]

        c_fn.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(GrugValueUnion),
        )
        c_fn.restype = GrugValueWorkaround

        return_type = self.state.mod_api.classes[class_name].methods[name].return_type # pyright: ignore

        self.state.mod_api.register_fn(class_name, name, self.wrap_fn(return_type, c_fn)) # pyright: ignore

    def _register_generic_method(self, class_name: str, name: str, native_name: str):
        c_reg_fn = self.grug_lib["reg_game_fn_" + native_name]
        c_reg_fn.argtypes = (ctypes.POINTER(CGrugType),)
        c_reg_fn.restype = ctypes.c_void_p

        host_fn_data = self.state.mod_api.classes[class_name].methods[name]

        def register(generics: List[Type]):
            c_generics: List[CGrugType] = []
            keepalive: List[object] = []
            for generic in generics:
                c_generic, generic_keepalive = py_type_to_c_type(generic)
                c_generics.append(c_generic)
                keepalive.extend(generic_keepalive)

            generic_array = (CGrugType * len(c_generics))(*c_generics)
            keepalive.append(generic_array)

            c_fn_ptr = c_reg_fn(generic_array)
            if c_fn_ptr is None:
                return None

            c_fn = game_fn_c_t(c_fn_ptr)
            return_type = substitute_type(host_fn_data.return_type, generics)

            return self.wrap_fn(return_type, c_fn) # pyright: ignore

        self.state.mod_api.register_generic_fn(class_name, name, register)


# Enables stepping through code with VS Code its Python debugger.
if __name__ == "__main__":  # pragma: no cover
    pytest.main(sys.argv)  # pyright: ignore[reportUnknownMemberType]
