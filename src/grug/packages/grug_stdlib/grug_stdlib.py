import math
from typing import Any, Callable, Dict, List, Tuple, TypeVar

from grug import GrugPackage
from grug.entity import GameFnError

try:
    from typing import Protocol  # Python >= 3.8
except ImportError:
    from typing_extensions import Protocol  # Python 3.7


# --------------------
# Assertions
# --------------------


def assert_bool(b1: bool, b2: bool):
    assert b1 == b2, f"assert_bool failed: {b1} != {b2}"


def assert_id(id1: object, id2: object):
    assert id1 == id2, f"assert_id failed: {id1} != {id2}"


def assert_number(n1: float, n2: float):
    assert n1 == n2, f"assert_number failed: {n1} != {n2}"


def assert_string(s1: str, s2: str):
    assert s1 == s2, f"assert_string failed: '{s1}' != '{s2}'"


# --------------------
# Math
# --------------------


def ceil(n: float) -> float:
    return float(math.ceil(n))


def sqrt(n: float) -> float:
    return math.sqrt(n)


# --------------------
# Dict core
# --------------------


def id_to_dict(id_: Dict[object, object]) -> Dict[object, object]:
    return id_


def dict_len(d: Dict[object, object]) -> float:
    return float(len(d))


def dict_X() -> Dict[object, object]:
    return {}


dict_X.__name__ = "dict"


def dict_set(d: Dict[object, object], key: object, val: object):
    d[key] = val


def dict_has_key(d: Dict[object, object], key: object) -> bool:
    return key in d


def dict_get(d: Dict[object, object], key: object) -> object:
    value = d.get(key)
    if value is None:
        raise GameFnError(
            f"dict_get({d}, {key}) failed, as key '{key}' is not in the Dict"
        )
    return value


def dict_get_default(d: Dict[object, object], key: object, default: object) -> object:
    return d.get(key, default)


def dict_set_default(d: Dict[object, object], key: object, val: object) -> object:
    return d.setdefault(key, val)


def dict_pop(d: Dict[object, object], key: object) -> object:
    return d.pop(key)


def dict_update(d: Dict[object, object], other: Dict[object, object]):
    d.update(other)


def dict_fromkeys(keys: List[object], val: object) -> Dict[object, object]:
    return dict.fromkeys(keys, val)


def dict_copy(d: Dict[object, object]) -> Dict[object, object]:
    return d.copy()


def dict_clear(d: Dict[object, object]):
    d.clear()


def dict_keys(d: Dict[object, object]) -> List[object]:
    return list(d.keys())


def dict_values(d: Dict[object, object]) -> List[object]:
    return list(d.values())


def dict_items(d: Dict[object, object]) -> List[List[object]]:
    return [[k, v] for k, v in d.items()]


def dict_popitem(d: Dict[object, object]) -> List[object]:
    k, v = d.popitem()
    return [k, v]


# --------------------
# List core
# --------------------


def id_to_list(id_: List[object]) -> List[object]:
    return id_


def list_clear(l: List[object]):
    l.clear()


def list_copy(l: List[object]) -> List[object]:
    return l.copy()


def list_extend(lst1: List[object], lst2: List[object]):
    lst1.extend(lst2)


def list_len(l: List[object]) -> float:
    return float(len(l))


def list_reverse(l: List[object]):
    l.reverse()


class SupportsLessThan(Protocol):
    def __lt__(self, __other: object) -> bool: ...


T = TypeVar("T", bound=SupportsLessThan)


def list_sort(l: List[T]):
    l.sort()


def list_X() -> List[object]:
    return []


list_X.__name__ = "list"


def list_append(l: List[object], val: object):
    l.append(val)


def list_count(l: List[object], val: object) -> float:
    return float(l.count(val))


def list_index(l: List[object], val: object) -> float:
    return float(l.index(val))


def list_insert(l: List[object], index: float, val: object):
    l.insert(int(index), val)


def list_pop(l: List[object]):
    return l.pop()


def list_pop_index(l: List[object], index: float):
    return l.pop(int(index))


def list_remove(l: List[object], val: object):
    l.remove(val)


# --------------------
# Printing
# --------------------


def print_bool(b: bool):
    print(b)


def print_id(id: object):
    print(id)


def format_number(x: object) -> object:
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x


def print_list(l: List[object]):
    print([format_number(x) for x in l])


def print_dict(d: Dict[object, object]):
    print({format_number(k): format_number(v) for k, v in d.items()})


def print_number(n: float):
    print(int(n) if n.is_integer() else n)


def print_string(s: str):
    print(s)


# --------------------
# Game fn registration
# --------------------


def assert_fns() -> List[Callable[..., Any]]:
    return [
        assert_bool,
        assert_id,
        assert_number,
        assert_string,
    ]


def casting_fns() -> List[Callable[..., Any]]:
    return [
        id_to_dict,
        id_to_list,
    ]


def math_fns() -> List[Callable[..., Any]]:
    return [
        ceil,
        sqrt,
    ]


def printing_fns() -> List[Callable[..., Any]]:
    return [
        print_bool,
        print_id,
        print_list,
        print_dict,
        print_number,
        print_string,
    ]


# --------------------
# Container registration
# --------------------


def wrap(fn: Callable[..., Any], name: str) -> Callable[..., Any]:
    def wrapper(*args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> Any:
        return fn(*args, **kwargs)

    wrapper.__name__ = name
    return wrapper


HASHABLE_TYPES = ("number", "bool", "string")
VALUE_TYPES = ("number", "bool", "string", "id")


def dict_fns() -> List[Callable[..., Any]]:
    fns: List[Callable[..., Any]] = []

    for fn in [
        dict_X,
        dict_len,
        dict_keys,
        dict_values,
        dict_items,
        dict_popitem,
        dict_update,
        dict_copy,
        dict_clear,
    ]:
        fns.append(fn)

    for value_type in VALUE_TYPES:
        fns.append(wrap(dict_pop, f"dict_{value_type}_pop"))
        fns.append(wrap(dict_fromkeys, f"dict_{value_type}_fromkeys"))

    for key_type in HASHABLE_TYPES:
        fns.append(wrap(dict_has_key, f"dict_{key_type}_has_key"))

        for value_type in VALUE_TYPES:
            fns.append(wrap(dict_get, f"dict_{key_type}_{value_type}_get"))
            fns.append(
                wrap(dict_get_default, f"dict_{key_type}_{value_type}_get_default")
            )
            fns.append(wrap(dict_set, f"dict_{key_type}_{value_type}_set"))
            fns.append(
                wrap(dict_set_default, f"dict_{key_type}_{value_type}_set_default")
            )

    return fns


def list_fns() -> List[Callable[..., Any]]:
    fns: List[Callable[..., Any]] = []

    for fn in [
        list_X,
        list_len,
        list_sort,
        list_clear,
        list_copy,
        list_extend,
        list_reverse,
    ]:
        fns.append(fn)

    for value_type in VALUE_TYPES:
        fns.append(wrap(list_append, f"list_{value_type}_append"))
        fns.append(wrap(list_count, f"list_{value_type}_count"))
        fns.append(wrap(list_index, f"list_{value_type}_index"))
        fns.append(wrap(list_insert, f"list_{value_type}_insert"))
        fns.append(wrap(list_pop, f"list_{value_type}_pop"))
        fns.append(wrap(list_pop_index, f"list_{value_type}_pop_index"))
        fns.append(wrap(list_remove, f"list_{value_type}_remove"))

    return fns


# --------------------
# Package
# --------------------


def get():
    game_fns: List[Callable[..., Any]] = []

    game_fns.extend(assert_fns())
    game_fns.extend(casting_fns())
    game_fns.extend(math_fns())
    game_fns.extend(printing_fns())

    # Containers
    game_fns.extend(dict_fns())
    game_fns.extend(list_fns())

    return GrugPackage(
        prefix="",
        game_fns=game_fns,
    )
