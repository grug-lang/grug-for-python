import math

from grug import GrugPackage


def print_number(n: float):
    print(n)


def ceil(n: float):
    return math.ceil(n)


def sqrt(n: float):
    return math.sqrt(n)


def get():
    return GrugPackage(prefix="std", game_fns=[print_number, ceil, sqrt])
