import ctypes
import numbers
from typing import Any, Callable, Dict, List, Union

from .frontend import ModApi

GrugValueType = Union[float, bool, str, int]


class GrugValue(ctypes.Union):
    _fields_ = [
        ("_number", ctypes.c_double),
        ("_bool", ctypes.c_bool),
        ("_string", ctypes.c_char_p),
        ("_id", ctypes.c_uint64),
    ]


GameFn = Callable[[ctypes.Array[GrugValue]], GrugValue]


class Backend:
    def __init__(self, mod_api: ModApi):
        self.mod_api = mod_api
        self.game_fns: Dict[str, Dict[str, Any]] = {}

    def register_game_fn(self, name: str, fn: GameFn):
        self.game_fns[name] = {
            "fn": fn,
            "return_type": self.mod_api["game_functions"][name].get("return_type"),
            "arg_types": [
                arg["type"]
                for arg in self.mod_api["game_functions"][name].get("arguments", [])
            ],
        }

    def init_globals_fn_dispatcher(self, path: str):
        pass

    def on_fn_dispatcher(
        self, on_fn_name: str, grug_file_path: str, args: List[GrugValueType]
    ):
        self.call_game_fn("initialize", [3])  # TODO: REMOVE!
        pass

    def call_game_fn(self, name: str, args: List[GrugValueType]):
        if name not in self.game_fns:
            raise KeyError(f"Unknown game function '{name}'")

        info = self.game_fns[name]
        fn: GameFn = info["fn"]

        # The fn args must be a ctypes array, not a Python list
        c_args = (GrugValue * len(args))()

        # TODO: Can this be removed?
        # Keeps strings alive
        string_refs: List[Any] = []

        for i, v in enumerate(args):
            if isinstance(v, bool):
                c_args[i]._bool = v
            elif isinstance(v, numbers.Real):
                c_args[i]._number = v
            elif isinstance(v, str):
                s = ctypes.c_char_p(v.encode())
                string_refs.append(s)
                c_args[i]._string = s
            elif isinstance(v, ctypes.c_uint64):
                c_args[i]._id = v
            else:
                raise TypeError(f"Unsupported arg type: {type(v)}")

        result = fn(c_args)

        return_type = info["return_type"]
        if return_type == "number":
            return result._number
        if return_type == "bool":
            return result._bool
        if return_type == "string":
            return result._string
        if return_type == "id":
            return result._id

        assert return_type == None
