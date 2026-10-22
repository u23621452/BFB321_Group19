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


# ---------- safety stock and reorder point ----------

def test_z_scores():
    assert m.z_for_service_level(0.95) == pytest.approx(1.645, abs=0.001)
    assert m.z_for_service_level(0.99) == pytest.approx(2.326, abs=0.001)


def test_z_rejects_bad_service_levels():
    with pytest.raises(ValueError):
        m.z_for_service_level(0.3)
    with pytest.raises(ValueError):
        m.z_for_service_level(1)


def test_safety_stock():
    # 1.645 * 4 * sqrt(9) = 1.645 * 12 = 19.74
    assert m.safety_stock(0.95, 4, 9) == pytest.approx(19.74, abs=0.01)


def test_safety_stock_is_zero_when_demand_never_varies():
    assert m.safety_stock(0.95, 0, 9) == 0


def test_reorder_point():
    # 10 per day * 9 days = 90, plus safety stock 19.74 = 109.74
    assert m.reorder_point(10, 9, 19.74) == pytest.approx(109.74)
    assert m.reorder_point(10, 9) == 90


def test_recommended_order_qty():
    # 141.42 rounds up to 142, then up to a whole number of 50-packs = 150
    assert m.recommended_order_qty(141.42, min_order_qty=50, pack_size=50) == 150
    # a small EOQ is raised to the supplier's minimum
    assert m.recommended_order_qty(12.3, min_order_qty=100) == 100
    # no minimum and no packs: just round up
    assert m.recommended_order_qty(12.3) == 13


# ---------- stock and reservations ----------

def test_available_stock():
    assert m.available_stock(100, 30) == 70


def test_available_stock_never_goes_below_zero():
    assert m.available_stock(10, 30) == 0


def test_job_with_enough_stock_has_no_shortage():
    bom = {"CU-WIND-01": 4, "FST-M8": 100}
    on_hand = {"CU-WIND-01": 10, "FST-M8": 500}
    assert m.check_job_availability(bom, on_hand) == []


def test_job_shortage_is_reported():
    bom = {"CU-WIND-01": 4, "FST-M8": 100}
    on_hand = {"CU-WIND-01": 10, "FST-M8": 500}
    reserved = {"CU-WIND-01": 8, "FST-M8": 350}
    result = m.check_job_availability(bom, on_hand, reserved)
    # CU-WIND-01: 10 - 8 = 2 free but 4 needed, so short by 2.
    # FST-M8: 500 - 350 = 150 free and 100 needed, so fine.
    assert len(result) == 1
    assert result[0]["sku"] == "CU-WIND-01"
    assert result[0]["available"] == 2
    assert result[0]["short_by"] == 2


def test_item_not_in_stock_counts_as_zero():
    result = m.check_job_availability({"NEW-PART": 5}, {})
    assert result[0]["short_by"] == 5


def test_reserve_job_adds_to_ledger_without_changing_the_original():
    ledger = {"A": 2}
    new_ledger = m.reserve_job({"A": 3, "B": 1}, ledger)
    assert new_ledger == {"A": 5, "B": 1}
    assert ledger == {"A": 2}


def test_below_reorder_point():
    assert m.below_reorder_point(50, 10, 40) is True    # 40 free, at the limit
    assert m.below_reorder_point(50, 5, 40) is False    # 45 free, above it