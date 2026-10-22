"""Tests for models/stock_model.py.

Each expected answer was worked out by hand first (see the comments), so the
tests check the model against the maths, not against itself.
Run from the stockflow folder with:  python -m pytest
"""
from datetime import date

import pytest

from models import stock_model as m


# ---------- EOQ and ordering costs ----------

def test_eoq():
    # sqrt(2 * 1200 * 50 / 6) = sqrt(20000) = 141.42
    assert m.calculate_eoq(1200, 50, 6) == pytest.approx(141.42, abs=0.01)


def test_eoq_rejects_zero_or_negative_inputs():
    with pytest.raises(ValueError):
        m.calculate_eoq(0, 50, 6)
    with pytest.raises(ValueError):
        m.calculate_eoq(1200, 0, 6)
    with pytest.raises(ValueError):
        m.calculate_eoq(1200, 50, -1)


def test_orders_per_year():
    # 1200 / 100 = 12 orders
    assert m.orders_per_year(1200, 100) == 12


def test_total_cost_at_eoq():
    # At the EOQ, ordering cost equals holding cost.
    # Total = sqrt(2 * 1200 * 50 * 6) = sqrt(720000) = 848.53
    eoq = m.calculate_eoq(1200, 50, 6)
    assert m.total_annual_cost(1200, 50, 6, eoq) == pytest.approx(848.53, abs=0.01)


def test_eoq_is_the_cheapest_order_size():
    eoq = m.calculate_eoq(1200, 50, 6)
    best = m.total_annual_cost(1200, 50, 6, eoq)
    assert m.total_annual_cost(1200, 50, 6, eoq / 2) > best
    assert m.total_annual_cost(1200, 50, 6, eoq * 2) > best


def test_total_cost_with_purchase_cost():
    # ordering (1200/100)*50 = 600, holding (100/2)*6 = 300, purchase 1200*2 = 2400
    assert m.total_annual_cost(1200, 50, 6, 100, unit_cost=2) == 3300