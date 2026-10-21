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

# ordering maths

def calculate_eoq(annual_demand, order_cost, holding_cost):
    """Economic Order Quantity = sqrt(2 * D * S / H).

    D = units used per year, S = cost of placing one order,
    H = cost of holding one unit for a year.
    """
    check_positive("annual_demand", annual_demand)
    check_positive("order_cost", order_cost)
    check_positive("holding_cost", holding_cost)
    return sqrt(2 * annual_demand * order_cost / holding_cost)


def orders_per_year(annual_demand, order_qty):
    """How many orders we place in a year = D / Q."""
    check_positive("annual_demand", annual_demand)
    check_positive("order_qty", order_qty)
    return annual_demand / order_qty


def total_annual_cost(annual_demand, order_cost, holding_cost, order_qty, unit_cost=0):
    """Ordering cost + holding cost (+ purchase cost if unit_cost is given)."""
    check_positive("annual_demand", annual_demand)
    check_positive("order_cost", order_cost)
    check_positive("holding_cost", holding_cost)
    check_positive("order_qty", order_qty)
    check_non_negative("unit_cost", unit_cost)

    ordering_cost = (annual_demand / order_qty) * order_cost
    holding_total = (order_qty / 2) * holding_cost
    purchase_cost = annual_demand * unit_cost
    return ordering_cost + holding_total + purchase_cost


def z_for_service_level(service_level):
    """Z-score for a service level, e.g. 0.95 gives about 1.645."""
    if service_level < 0.5 or service_level >= 1:
        raise ValueError("service_level must be from 0.5 up to (not including) 1")
    return NormalDist().inv_cdf(service_level)


def safety_stock(service_level, daily_demand_std, lead_time_days):
    """Extra stock kept in case demand is higher than normal.

    Safety stock = Z * daily demand spread * sqrt(lead time).
    """
    check_non_negative("daily_demand_std", daily_demand_std)
    check_positive("lead_time_days", lead_time_days)
    z = z_for_service_level(service_level)
    return z * daily_demand_std * sqrt(lead_time_days)


def reorder_point(daily_demand, lead_time_days, safety_stock_units=0):
    """Stock level at which we should reorder = demand during lead time + safety stock."""
    check_non_negative("daily_demand", daily_demand)
    check_positive("lead_time_days", lead_time_days)
    check_non_negative("safety_stock_units", safety_stock_units)
    return daily_demand * lead_time_days + safety_stock_units


def recommended_order_qty(eoq, min_order_qty=1, pack_size=1):
    """Round the EOQ up to something we can actually buy.

    It must be at least the supplier's minimum, and a whole number of packs.
    """
    check_positive("eoq", eoq)
    check_positive("min_order_qty", min_order_qty)
    check_positive("pack_size", pack_size)
    qty = max(ceil(eoq), min_order_qty)
    return int(ceil(qty / pack_size) * pack_size)

# stock and reservations

def available_stock(on_hand, reserved):
    """Free stock = what is on the shelf minus what is already reserved."""
    check_non_negative("on_hand", on_hand)
    check_non_negative("reserved", reserved)
    return max(on_hand - reserved, 0)


def check_job_availability(bom, on_hand, reserved=None):
    """Check a job's materials list against stock.

    bom      = {sku: quantity the job needs}
    on_hand  = {sku: quantity physically in the storeroom}
    reserved = {sku: quantity already reserved by other jobs}

    Returns a list with one dictionary per short item. The list is empty
    when everything is covered. An item missing from on_hand counts as zero.
    """
    if reserved is None:
        reserved = {}

    shortages = []
    for sku, required in bom.items():
        check_non_negative("required quantity for " + sku, required)
        free = available_stock(on_hand.get(sku, 0), reserved.get(sku, 0))
        if required > free:
            shortages.append({
                "sku": sku,
                "required": required,
                "available": free,
                "short_by": required - free,
            })
    return shortages


def reserve_job(bom, reserved):
    """Return a new reservation dictionary with this job's items added.

    The dictionary you pass in is left unchanged.
    """
    updated = dict(reserved)
    for sku, qty in bom.items():
        check_non_negative("required quantity for " + sku, qty)
        updated[sku] = updated.get(sku, 0) + qty
    return updated


def below_reorder_point(on_hand, reserved, reorder_point_units):
    """True when free stock is at or below the reorder point."""
    check_non_negative("reorder_point_units", reorder_point_units)
    return available_stock(on_hand, reserved) <= reorder_point_units


# planning window

def jobs_in_window(jobs, today, window_days=7):
    """Jobs that start from today up to window_days from today, earliest first.

    Each job is a dictionary with a 'start_date' (a date).
    """
    check_positive("window_days", window_days)
    last_day = today + timedelta(days=window_days)

    in_window = []
    for job in jobs:
        if today <= job["start_date"] <= last_day:
            in_window.append(job)

    return sorted(in_window, key=lambda job: job["start_date"])


# KPIs

def inventory_record_accuracy(system_counts, physical_counts):
    """Percentage of items where the system count matches the physical count."""
    all_skus = set(system_counts) | set(physical_counts)
    if len(all_skus) == 0:
        raise ValueError("no SKUs supplied")

    matches = 0
    for sku in all_skus:
        if system_counts.get(sku, 0) == physical_counts.get(sku, 0):
            matches += 1
    return 100 * matches / len(all_skus)


def percent_change(before, after):
    """Percentage change from a starting value, e.g. 45 to 10 gives -77.8."""
    if before == 0:
        raise ValueError("starting value must not be zero")
    return 100 * (after - before) / before