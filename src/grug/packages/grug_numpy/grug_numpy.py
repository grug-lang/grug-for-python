import numpy

from grug import GrugPackage


def exp(n: float):
    return numpy.exp(n)


def get():
    return GrugPackage(prefix="np", game_fns=[exp])
