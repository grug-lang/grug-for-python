import math
from typing import Dict, List, Tuple, TypeVar, cast

from dataclasses import dataclass
from grug import GrugPackage, GrugState
from grug.entity import GameFnError

from grug.parser import Type
from grug.grug_value import GrugValue, HostFn, HostFnReg

try:
    from typing import Protocol  # Python >= 3.8
except ImportError:  # pragma: no cover
    from typing_extensions import Protocol  # Python 3.7

# --------------------
# Type classes
# --------------------

@dataclass
class Pair:
    first: object
    second: object

def make_pair(types: List[Type]) -> HostFn:
    def inner(state: GrugState, first: object, second: object):
        return Pair(first, second)
    return inner

def pair_first(types: List[Type]) -> HostFn:
    def inner(state: GrugState, pair: Pair):
        return pair.first
    return inner

def pair_second(types: List[Type]) -> HostFn:
    def inner(state: GrugState, pair: Pair):
        return pair.second
    return inner

pair_first.__name__ = "first"
pair_second.__name__ = "second"

# --------------------
# Assertions
# --------------------

def assert_(state: GrugState, value: bool):
    assert value, "assert failed"

assert_.__name__ = "assert"


def assert_eq(types: List[Type]) -> HostFn:
    def eq(state: GrugState, v1: GrugValue, v2: GrugValue):
        assert v1 == v2, f"assert failed {v1} != {v2}"

    return eq

# --------------------
# Math
# --------------------


def ceil(state: GrugState, n: float) -> float:
    return float(math.ceil(n))


def sqrt(state: GrugState, n: float) -> float:
    return math.sqrt(n)


# --------------------
# Dict core
# --------------------

def dict_len(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> float:
        return float(len(d))

    return inner


def dict_X(types: List[Type]) -> HostFn:
    def inner(state: GrugState) -> Dict[object, object]:
        return {}

    return inner


dict_X.__name__ = "dict"


def dict_set(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object], key: object, val: object):
        d[key] = val

    return inner


def dict_has_key(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object], key: object) -> bool:
        return key in d

    return inner


def dict_get(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object], key: object) -> object:
        try:
            return d[key]
        except KeyError:
            raise GameFnError(
                f"dict_get({d}, {key}) failed, as key '{key}' is not in the Dict"
            )

    return inner


def dict_get_or_default(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState, d: Dict[object, object], key: object, default: object
    ) -> object:
        return d.get(key, default)

    return inner


def dict_set_if_empty(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState, d: Dict[object, object], key: object, val: object
    ) -> bool:
        if key in d:
            return False
        d[key] = val
        return True

    return inner


def dict_pop(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object], key: object) -> object:
        return d.pop(key)

    return inner


def dict_update(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState,
        d: Dict[object, object],
        other: Dict[object, object],
    ):
        d.update(other)

    return inner


def dict_fromkeys(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState, keys: List[object], val: object
    ) -> Dict[object, object]:
        return dict.fromkeys(keys, val)

    return inner


dict_fromkeys.__name__ = "dict_from_keys"


def dict_copy(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> Dict[object, object]:
        return d.copy()

    return inner


def dict_clear(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]):
        d.clear()

    return inner


def dict_keys(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> List[object]:
        return list(d.keys())

    return inner


def dict_values(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> List[object]:
        return list(d.values())

    return inner


def dict_items(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> List[Pair[object, object]]:
        return [Pair(first=k, second=v) for k, v in d.items()]

    return inner


def dict_pop_item(types: List[Type]) -> HostFn:
    def inner(state: GrugState, d: Dict[object, object]) -> List[object]:
        k, v = d.popitem()
        return Pair(first=k, second=v)

    return inner


dict_has_key.__name__ = "has_key"
dict_set.__name__ = "set"
dict_set_if_empty.__name__ = "set_if_empty"
dict_get.__name__ = "get"
dict_get_or_default.__name__ = "get_or_default"
dict_clear.__name__ = "clear"
dict_len.__name__ = "len"
dict_pop.__name__ = "pop"
dict_pop_item.__name__ = "pop_item"
dict_keys.__name__ = "keys"
dict_values.__name__ = "values"
dict_items.__name__ = "items"
dict_update.__name__ = "update"
dict_copy.__name__ = "copy"

# --------------------
# List core
# --------------------


def list_clear(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object]):
        values.clear()

    return inner


def list_copy(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object]) -> List[object]:
        return values.copy()

    return inner


def list_has(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], value: object) -> bool:
        return value in values

    return inner


def list_extend(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState, values: List[object], other_values: List[object]
    ):
        values.extend(other_values)

    return inner


def list_len(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object]) -> float:
        return float(len(values))

    return inner


def list_reverse(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object]):
        values.reverse()

    return inner


class SupportsLessThan(Protocol):
    def __lt__(self, __other: object) -> bool: ...  # pragma: no cover


T = TypeVar("T", bound=SupportsLessThan)


def list_sort(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[T]):
        values.sort()

    return inner


def list_X(types: List[Type]) -> HostFn:
    def inner(state: GrugState) -> List[object]:
        return []

    return inner


list_X.__name__ = "list"


def list_append(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], val: object):
        values.append(val)

    return inner


def list_count(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], val: object) -> float:
        return float(values.count(val))

    return inner


def list_index(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], val: object) -> float:
        return float(values.index(val))

    return inner


def list_insert(types: List[Type]) -> HostFn:
    def inner(
        state: GrugState, values: List[object], index: float, val: object
    ):
        values.insert(int(index), val)

    return inner


def list_pop(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object]) -> object:
        return values.pop()

    return inner


def list_pop_index(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], index: float) -> object:
        return values.pop(int(index))

    return inner


def list_remove(types: List[Type]) -> HostFn:
    def inner(state: GrugState, values: List[object], val: object):
        values.remove(val)

    return inner


list_len.__name__ = "len"
list_sort.__name__ = "sort"
list_clear.__name__ = "clear"
list_copy.__name__ = "copy"
list_extend.__name__ = "extend"
list_reverse.__name__ = "reverse"
list_append.__name__ = "append"
list_count.__name__ = "count"
list_has.__name__ = "has"
list_index.__name__ = "index"
list_insert.__name__ = "insert"
list_pop.__name__ = "pop"
list_pop_index.__name__ = "pop_index"
list_remove.__name__ = "remove"


# --------------------
# Printing
# --------------------

def format_number(x: object) -> object:
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x

def print_value(types: List[Type]) -> HostFn:
    def inner(state: GrugState, value: GrugValue):
        if isinstance(value, float):
            print(format_number(value))
        elif isinstance(value, list):
            values = cast(List[object], value)
            print([format_number(item) for item in values])
        elif isinstance(value, dict):
            values_by_key = cast(Dict[object, object], value)
            print(
                {
                    format_number(key): format_number(item)
                    for key, item in values_by_key.items()
                }
            )
        else:
            print(value)

    return inner


print_value.__name__ = "print"

# --------------------
# Container registration
# --------------------


def dict_fns() -> List[HostFnReg]:
    return [
        dict_X,
        dict_fromkeys,
    ]

def dict_methods() -> List[Tuple[str, HostFnReg]]:
    return [
        ("Dict", dict_has_key),
        ("Dict", dict_set),
        ("Dict", dict_set_if_empty),
        ("Dict", dict_get),
        ("Dict", dict_get_or_default),
        ("Dict", dict_clear),
        ("Dict", dict_len),
        ("Dict", dict_pop),
        ("Dict", dict_pop_item),
        ("Dict", dict_keys),
        ("Dict", dict_values),
        ("Dict", dict_items),
        ("Dict", dict_update),
        ("Dict", dict_copy),
    ]


def list_fns() -> List[HostFnReg]:
    return [
        list_X,
    ]


def list_methods() -> List[Tuple[str, HostFnReg]]:
    return [
        ("List", list_len),
        ("List", list_sort),
        ("List", list_clear),
        ("List", list_copy),
        ("List", list_extend),
        ("List", list_reverse),
        ("List", list_append),
        ("List", list_count),
        ("List", list_has),
        ("List", list_index),
        ("List", list_insert),
        ("List", list_pop),
        ("List", list_pop_index),
        ("List", list_remove),
    ]


# --------------------
# Package
# --------------------


def get():
    host_fns: List[HostFn] = []
    generic_fns: List[HostFnReg] = [assert_eq, print_value]

    # bare assert function
    host_fns.append(assert_)
    # math functions
    host_fns.extend([ceil, sqrt])

    generic_fns.extend(dict_fns())
    generic_fns.extend(list_fns())
    generic_fns.extend([make_pair])
    generic_methods = dict_methods()
    generic_methods.extend(list_methods())
    generic_methods.extend([("Pair", pair_first), ("Pair", pair_second)])

    return GrugPackage(
        prefix="",
        host_fns=host_fns,
        generic_fns=generic_fns,
        methods=[],
        generic_methods=generic_methods,
    )
