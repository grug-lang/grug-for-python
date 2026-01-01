import math
from typing import Any, Callable, Dict, List, Protocol, Tuple, TypeVar

from grug import GrugPackage


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
    return math.ceil(n)


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
    print(n)


def print_string(s: str):
    print(s)


# Generic list print implementation
def _print_list(lst: List[object]):
    print([int(x) if isinstance(x, float) and x.is_integer() else x for x in lst])


# Type-specific list print wrappers
def print_list_number(lst: List[object]):
    _print_list(lst)


def print_list_bool(lst: List[object]):
    _print_list(lst)


def print_list_string(lst: List[object]):
    _print_list(lst)


def print_list_id(lst: List[object]):
    _print_list(lst)


# -------------------------
# Generic list operations
# -------------------------
def list_X() -> List[object]:
    return []


def list_append(lst: List[object], val: object):
    lst.append(val)


def list_len(lst: List[object]) -> float:
    return len(lst)


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
    return lst.index(val)


def list_count(lst: List[object], val: object) -> float:
    return lst.count(val)


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
        (f"list_{type_name}", wrap(list_X)),
        (f"list_{type_name}_append", wrap(list_append)),
        (f"list_{type_name}_len", wrap(list_len)),
        (f"list_{type_name}_extend", wrap(list_extend)),
        (f"list_{type_name}_insert", wrap(list_insert)),
        (f"list_{type_name}_remove", wrap(list_remove)),
        (f"list_{type_name}_pop", wrap(list_pop)),
        (f"list_{type_name}_pop_index", wrap(list_pop_index)),
        (f"list_{type_name}_index", wrap(list_index)),
        (f"list_{type_name}_count", wrap(list_count)),
        (f"list_{type_name}_sort", wrap(list_sort)),
        (f"list_{type_name}_reverse", wrap(list_reverse)),
        (f"list_{type_name}_copy", wrap(list_copy)),
        (f"list_{type_name}_clear", wrap(list_clear)),
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
        print_number,
        print_bool,
        print_string,
        print_id,
        # register all 4 type-specific print_list functions
        print_list_number,
        print_list_bool,
        print_list_string,
        print_list_id,
        ceil,
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
