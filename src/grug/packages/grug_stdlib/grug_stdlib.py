import math
from typing import List

from grug import GrugPackage


def assert_bool(b1: bool, b2: bool):
    assert b1 == b2, f"assert_bool failed: {b1} != {b2}"


def assert_id(id1: object, id2: object):
    assert id1 == id2, f"assert_id failed: {id1} != {id2}"


def assert_number(n1: float, n2: float):
    assert n1 == n2, f"assert_number failed: {n1} != {n2}"


def assert_string(s1: str, s2: str):
    assert s1 == s2, f"assert_string failed: '{s1}' != '{s2}'"


def ceil(n: float) -> float:
    return math.ceil(n)


def list_number_append(lst: List[float], n: float):
    lst.append(n)


def list_number_clear(lst: List[float]):
    lst.clear()


def list_number_copy(lst: List[float]) -> List[float]:
    return lst.copy()


def list_number_count(lst: List[float], n: float) -> float:
    return lst.count(n)


def list_number_extend(lst1: List[float], lst2: List[float]):
    lst1.extend(lst2)


def list_number_index(lst: List[float], n: float) -> float:
    return lst.index(n)


def list_number_insert(lst: List[float], index: float, n: float):
    lst.insert(int(index), n)


def list_number_len(lst: List[float]) -> float:
    return len(lst)


def list_number_pop_index(lst: List[float], index: float) -> float:
    return lst.pop(int(index))


def list_number_pop(lst: List[float]) -> float:
    return lst.pop()


def list_number_remove(lst: List[float], n: float):
    lst.remove(n)


def list_number_reverse(lst: List[float]):
    lst.reverse()


def list_number_sort(lst: List[float]):
    lst.sort()


def list_number() -> List[float]:
    return []


def print_bool(b: bool):
    print(b)


def print_id(id: int):
    print(id)


def print_list_number(lst: List[float]):
    print([int(x) if x.is_integer() else x for x in lst])


def print_number(n: float):
    print(n)


def print_string(s: str):
    print(s)


def sqrt(n: float) -> float:
    return math.sqrt(n)


def get():
    return GrugPackage(
        prefix="",
        game_fns=[
            assert_bool,
            assert_id,
            assert_number,
            assert_string,
            print_number,
            print_bool,
            print_string,
            print_id,
            print_list_number,
            list_number,
            list_number_append,
            list_number_len,
            list_number_extend,
            list_number_insert,
            list_number_remove,
            list_number_pop,
            list_number_pop_index,
            list_number_index,
            list_number_count,
            list_number_sort,
            list_number_reverse,
            list_number_copy,
            list_number_clear,
            ceil,
            sqrt,
        ],
    )
