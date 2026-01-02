import math
from typing import Any, Callable, Dict, List, Tuple, TypeVar

from grug import GrugPackage

try:
    from typing import Protocol  # Python >= 3.8
except ImportError:
    from typing_extensions import Protocol  # Python 3.7


# -------------------------
# Asserts
# -------------------------
def assert_bool(b1: bool, b2: bool):
    assert b1 == b2, f"assert_bool failed: {b1} != {b2}"


def assert_id(id1: object, id2: object):
    assert id1 == id2, f"assert_id failed: {id1} != {id2}"


def assert_number(n1: float, n2: float):
    assert n1 == n2, f"assert_number failed: {n1} != {n2}"


def assert_string(s1: str, s2: str):
    assert s1 == s2, f"assert_string failed: '{s1}' != '{s2}'"


# -------------------------
# Math
# -------------------------
def ceil(n: float) -> float:
    return float(math.ceil(n))


def sqrt(n: float) -> float:
    return math.sqrt(n)


# -------------------------
# Print functions
# -------------------------
def print_bool(b: bool):
    print(b)


def print_id(id: object):
    print(id)


def print_number(n: float):
    print(int(n) if n.is_integer() else n)


def print_string(s: str):
    print(s)


# Generic list print implementation
def _print_list(lst: List[object]):
    print([int(x) if isinstance(x, float) and x.is_integer() else x for x in lst])


def print_list(lst: List[object]):
    _print_list(lst)


# -------------------------
# Casting
# -------------------------


def id_to_list(id_: List[object]) -> List[object]:
    # TODO: Throw if id is not a List, though idk which file should own the id->type map
    return id_


# -------------------------
# Generic list operations
# -------------------------
def list_X() -> List[object]:
    return []


# This renaming trick allows the Python3 list() to still be used
list_X.__name__ = "list"


def list_append(lst: List[object], val: object):
    lst.append(val)


def list_len(lst: List[object]) -> float:
    return float(len(lst))


def list_extend(lst1: List[object], lst2: List[object]):
    lst1.extend(lst2)


def list_insert(lst: List[object], index: float, val: object):
    lst.insert(int(index), val)


def list_remove(lst: List[object], val: object):
    lst.remove(val)


def list_pop(lst: List[object]):
    return lst.pop()


def list_pop_index(lst: List[object], index: float):
    return lst.pop(int(index))


def list_index(lst: List[object], val: object) -> float:
    return float(lst.index(val))


def list_count(lst: List[object], val: object) -> float:
    return float(lst.count(val))


# Define a Comparable protocol
class SupportsLessThan(Protocol):
    def __lt__(self, __other: object) -> bool: ...


# TypeVar bound to comparable objects
T = TypeVar("T", bound=SupportsLessThan)


def list_sort(lst: List[T]):
    lst.sort()


def list_reverse(lst: List[object]):
    lst.reverse()


def list_copy(lst: List[object]) -> List[object]:
    return lst.copy()


def list_clear(lst: List[object]):
    lst.clear()


# -------------------------
# Factory to generate unique list functions per type
# -------------------------
def make_list_package(type_name: str) -> List[Tuple[str, Callable[..., Any]]]:
    """Return a list of freshly wrapped functions for the given type."""

    def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> Any:
            return fn(*args, **kwargs)

        return wrapper

    return [
        (f"list_{type_name}_append", wrap(list_append)),
        (f"list_{type_name}_count", wrap(list_count)),
        (f"list_{type_name}_index", wrap(list_index)),
        (f"list_{type_name}_insert", wrap(list_insert)),
        (f"list_{type_name}_pop", wrap(list_pop)),
        (f"list_{type_name}_pop_index", wrap(list_pop_index)),
        (f"list_{type_name}_remove", wrap(list_remove)),
    ]


# -------------------------
# Package registration
# -------------------------
def get():
    game_fns = [
        assert_bool,
        assert_id,
        assert_number,
        assert_string,
        ceil,
        id_to_list,
        list_clear,
        list_copy,
        list_extend,
        list_len,
        list_reverse,
        list_sort,
        list_X,
        print_bool,
        print_id,
        print_list,
        print_number,
        print_string,
        sqrt,
    ]

    # Register list functions for multiple types
    for type_name in ["number", "bool", "string", "id"]:
        for fn_name, fn in make_list_package(type_name):
            fn.__name__ = fn_name
            game_fns.append(fn)

    return GrugPackage(
        prefix="",
        game_fns=game_fns,
    )
