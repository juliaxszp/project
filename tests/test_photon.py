from src.photon import *
from pysat.solvers import Kissat404
from pysat.formula import CNF, IDPool


def test_add_constant():
    builder = Builder()

