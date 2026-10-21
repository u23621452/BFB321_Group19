"""StockFlow supply chain model.

Plain Python calculations for the storeroom.
"""

from datetime import timedelta
from math import ceil, sqrt
from statistics import NormalDist


# small checks to be used

def check_positive(name, value):
    if value is None or value <= 0:
        raise ValueError(name + " must be greater than zero")


def check_non_negative(name, value):
    if value is None or value < 0:
        raise ValueError(name + " must not be negative")