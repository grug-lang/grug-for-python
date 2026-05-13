import argparse
import ctypes
import json
import sys
import os
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, cast

ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
TESTS_DIR = ROOT / "tests"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(TESTS_DIR))

import grug
from grug.entity import Entity, ReraisedGameFnError, StackOverflow, TimeLimitExceeded
from grug.grug_state import GrugFile, GrugRuntimeErrorType, GrugState
from grug.grug_value import GrugValue
from test_grug import (  # pyright: ignore[reportMissingImports]
    GrugValueUnion,
    GrugValueWorkaround,
    c_to_py_value,
)


# typedef void* (*create_grug_state_t)(const char* mod_api_path, const char* mods_dir);
create_grug_state_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
)
# typedef void (*destroy_grug_state_t)(void* state);
destroy_grug_state_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p)
# typedef void* (*compile_grug_file_t)(void* state, const char* file_path);
compile_grug_file_t = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)
# typedef void* (*create_entity_t)(void* state, void* grug_script_id);
create_entity_t = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
# typedef void* (*get_on_fn_id_t)(void* state, const char* entity_type, const char* function_name);
get_on_fn_id_t = ctypes.CFUNCTYPE(
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p
)
# typedef void (*call_entity_on_fn_t)(void* state, void* entity, void* on_fn_id, union grug_value* value, size_t values_len);
call_entity_on_fn_t = ctypes.CFUNCTYPE(
    None,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.POINTER(GrugValueUnion),
    ctypes.c_size_t,
)
# typedef void (*destroy_entity_t)(void* state, void* entity);
destroy_entity_t = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


class BenchmarkStateVTableStruct(ctypes.Structure):
    """
    Corresponds to struct grug_state_vtable in grug-bench/bench.h.
    """

    _fields_ = [
        ("create_grug_state", create_grug_state_t),
        ("destroy_grug_state", destroy_grug_state_t),
        ("compile_grug_file", compile_grug_file_t),
        ("create_entity", create_entity_t),
        ("get_on_fn_id", get_on_fn_id_t),
        ("call_entity_on_fn", call_entity_on_fn_t),
        ("destroy_entity", destroy_entity_t),
    ]


class BenchmarkArgs(NamedTuple):
    grug_bench_path: Path


def load_benchmark_lib(lib_path: Path) -> ctypes.PyDLL:
    if not lib_path.is_file():
        raise FileNotFoundError(f"Shared library not found: {lib_path}")

    lib = ctypes.PyDLL(str(lib_path))

    lib.runtime_error_handler.argtypes = [
        ctypes.c_char_p,  # reason
        ctypes.c_int,  # grug_runtime_error_type
        ctypes.c_char_p,  # on_fn_name
        ctypes.c_char_p,  # on_fn_path
    ]
    lib.runtime_error_handler.restype = None

    lib.grug_bench_run.argtypes = [
        ctypes.c_char_p,  # mod_api_path
        ctypes.c_char_p,  # mods_dir
        ctypes.POINTER(BenchmarkStateVTableStruct),
        ctypes.c_bool,  # headless
    ]
    lib.grug_bench_run.restype = None

    return lib


def normalized_mod_api_path(mod_api_path: Path) -> Path:
    with mod_api_path.open() as f:
        mod_api = json.load(f)

    entities = cast(Dict[str, Dict[str, Any]], mod_api.get("entities", {}))
    for entity in entities.values():
        on_functions = entity.get("on_functions")
        if isinstance(on_functions, list):
            entity["on_functions"] = sorted(on_functions, key=lambda fn: fn["name"])

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    )
    with temp_file:
        json.dump(mod_api, temp_file)

    return Path(temp_file.name)

def parse_args() -> BenchmarkArgs:
    parser = argparse.ArgumentParser(description="Run grug benchmark harness for Python.")
    parser.add_argument(
        "--grug-bench-path",
        "--grug-benchmarks-path",
        dest="grug_bench_path",
        required=True,
        type=Path,
        help="Path to the grug-bench repository",
    )
    parsed_args = vars(parser.parse_args())
    return BenchmarkArgs(
        grug_bench_path=cast(Path, parsed_args["grug_bench_path"]),
    )

def run_benchmarks(mod_api_path: str, mods_dir_path: str, benchmark_lib: ctypes.PyDLL):
    benchmark_lib = benchmark_lib

    state: Optional[GrugState] = None

    file_by_id: Dict[int, GrugFile] = {}
    entity_by_id: Dict[int, Entity] = {}
    on_fn_by_id: Dict[int, str] = {}

    _next_id = 1

    def _runtime_error_handler(
        reason: str,
        grug_runtime_error_type: GrugRuntimeErrorType,
        on_fn_name: str,
        on_fn_path: str,
    ) -> None:
        benchmark_lib.runtime_error_handler(
            reason.encode(),
            grug_runtime_error_type.value,
            on_fn_name.encode(),
            on_fn_path.encode(),
        )

    def _allocate_id() -> int:
        nonlocal _next_id
        allocated_id = _next_id
        _next_id += 1
        return allocated_id

    @create_grug_state_t
    def create_grug_state(mod_api_path: bytes, mods_dir: bytes) -> int:
        nonlocal state
        nonlocal benchmark_lib
        try:
            state = grug.init(
                runtime_error_handler=_runtime_error_handler,
                mod_api_path=ctypes.string_at(mod_api_path).decode(),
                mods_dir_path=ctypes.string_at(mods_dir).decode(),
                on_fn_time_limit_ms=10_000,
            )
            BenchmarkGameFnRegistrator(state, benchmark_lib).register_game_fns()
            return 1
        except Exception:  
            traceback.print_exc(file=sys.stderr)
            os._exit(2)
        return 0

    @destroy_grug_state_t
    def destroy_grug_state(state_ptr: int) -> None:
        nonlocal state
        nonlocal file_by_id
        nonlocal entity_by_id
        nonlocal on_fn_by_id
        state = None
        file_by_id.clear()
        entity_by_id.clear()
        on_fn_by_id.clear()

    @compile_grug_file_t
    def compile_grug_file(state_ptr: int, file_path: bytes) -> int:
        nonlocal state
        nonlocal file_by_id
        try:
            assert state
            file_id = _allocate_id()
            file_by_id[file_id] = state.compile_grug_file(
                ctypes.string_at(file_path).decode()
            )
            return file_id
        except Exception:  
            traceback.print_exc(file=sys.stderr)
            os._exit(2)

    @create_entity_t
    def create_entity(state_ptr: int, grug_script_id: int) -> int:
        nonlocal entity_by_id
        nonlocal file_by_id
        try:
            entity_id = _allocate_id()
            entity_by_id[entity_id] = file_by_id[grug_script_id].create_entity()
            return entity_id
        except Exception:  
            traceback.print_exc(file=sys.stderr)
            os._exit(2)

    @get_on_fn_id_t
    def get_on_fn_id(state_ptr: int, entity_type: bytes, function_name: bytes) -> int:
        nonlocal on_fn_by_id
        on_fn_id = _allocate_id()
        on_fn_by_id[on_fn_id] = ctypes.string_at(function_name).decode()
        return on_fn_id

    @call_entity_on_fn_t
    def call_entity_on_fn(
        state_ptr: int,
        entity_id: int,
        on_fn_id: int,
        c_args: List[GrugValueUnion],
        args_len: int,
    ) -> None:
        nonlocal entity_by_id
        nonlocal on_fn_by_id
        try:
            entity = entity_by_id[entity_id]
            on_fn_name = on_fn_by_id[on_fn_id]
            on_fn_decl = entity.file.on_fns[on_fn_name]
            assert len(on_fn_decl.arguments) == args_len
            args = [
                c_to_py_value(arg, argument.type_name)
                for arg, argument in zip(c_args or [], on_fn_decl.arguments)
            ]
            entity._run_on_fn(on_fn_name, *args)  # pyright: ignore[reportPrivateUsage]
        except (TimeLimitExceeded, StackOverflow, ReraisedGameFnError):
            os._exit(2)

    @destroy_entity_t
    def destroy_entity(state_ptr: int, entity_id: int) -> None:
        nonlocal entity_by_id
        entity_by_id.pop(entity_id, None)

    vtable = BenchmarkStateVTableStruct(
        create_grug_state,
        destroy_grug_state,
        compile_grug_file,
        create_entity,
        get_on_fn_id,
        call_entity_on_fn,
        destroy_entity,
    )

    benchmark_lib.grug_bench_run(
        str(mod_api_path).encode(),
        str(mods_dir_path).encode(),
        ctypes.byref(vtable),
        1
    )

class BenchmarkGameFnRegistrator:
    def __init__(self, state: GrugState, benchmark_lib: ctypes.PyDLL):
        self.state = state
        self.benchmark_lib = benchmark_lib

    def register_game_fns(self) -> None:
        for name in self.state.mod_api["game_functions"]:
            self._register_fn(name)

    def _get_c_args(self, *args: GrugValue):
        c_args = (GrugValueUnion * len(args))()

        for i, value in enumerate(args):
            if isinstance(value, float):
                c_args[i]._number = value
            elif isinstance(value, bool):
                c_args[i]._bool = value
            else:
                assert isinstance(value, int)
                c_args[i]._id = ctypes.c_uint64(value)

        return c_args

    def _unpack_workaround(
        self, c_workaround: GrugValueWorkaround, return_type: Optional[str]
    ) -> Optional[GrugValue]:
        if return_type is None:
            return None

        value = GrugValueUnion()
        ctypes.memmove(
            ctypes.byref(value), ctypes.byref(c_workaround), ctypes.sizeof(value)
        )
        return c_to_py_value(value, return_type)

    def _register_fn(self, name: str) -> None:
        c_fn = self.benchmark_lib["game_fn_" + name]

        c_fn.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(GrugValueUnion),
        )
        c_fn.restype = GrugValueWorkaround

        return_type = self.state.mod_api["game_functions"][name].get("return_type")

        def fn(state: GrugState, *args: GrugValue) -> Optional[GrugValue]:
            del state
            c_args = self._get_c_args(*args)
            result: GrugValueWorkaround = c_fn(0, c_args)
            return self._unpack_workaround(result, return_type)

        self.state._register_game_fn(name, fn)  # pyright: ignore[reportPrivateUsage]

def main() -> None:
    args = parse_args()

    grug_bench_path = args.grug_bench_path
    if not grug_bench_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {grug_bench_path}")

    if sys.platform == "win32":  
        lib_path = grug_bench_path / "build/bench.dll"
    elif sys.platform == "linux":  
        lib_path = grug_bench_path / "build/libbench.so"
    else:
        raise RuntimeError(f"Unsupported operating system: {sys.platform}")  

    benchmark_lib = load_benchmark_lib(lib_path)
    run_benchmarks(
        grug_bench_path / "mod_api.json",
        grug_bench_path / "mods",
        benchmark_lib,
    )

if __name__ == "__main__":
    main()
