import numpy

from grug import GrugPackage, GrugState


def exp(state: GrugState, n: float):
    return numpy.exp(n)


def get():
    return GrugPackage(prefix="np", game_fns=[exp])
