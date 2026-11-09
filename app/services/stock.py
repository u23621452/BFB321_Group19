"""Stock calculations that need the database.
The maths itself lives in models/stock_model.py - this file only feeds it."""
from app.extensions import db
from app.models import Product, Job, JobLine
from models import stock_model as sm

ACTIVE_STATUSES = ("reserved", "shortage", "kitting")
SERVICE_LEVEL = 0.95


def reserved_by_product():
    """{product_id: units promised to open jobs but not yet picked}"""
    rows = (db.session.query(JobLine.product_id, JobLine.qty, JobLine.picked_qty)
            .join(Job, Job.id == JobLine.job_id)
            .filter(Job.status.in_(ACTIVE_STATUSES))
            .all())
    reserved = {}
    for product_id, qty, picked in rows:
        reserved[product_id] = reserved.get(product_id, 0) + (qty - picked)
    return reserved


def inventory_row(product, reserved):
    """One product turned into the numbers shown on the inventory page."""
    available = sm.available_stock(product.on_hand, reserved)

    safety = sm.safety_stock(SERVICE_LEVEL, product.daily_demand_std,
                             product.lead_time_days)
    rop = sm.reorder_point(product.daily_demand, product.lead_time_days, safety)
    eoq = sm.calculate_eoq(product.annual_demand, product.order_cost,
                           product.holding_cost)
    order_qty = sm.recommended_order_qty(eoq, product.min_order_qty,
                                         product.pack_size)

    if available <= 0.5 * rop:
        status = "critical"
    elif available <= rop:
        status = "low"
    else:
        status = "ok"

    return {
        "id": product.id,
        "sku": product.sku,
        "description": product.description,
        "bin": product.bin_location,
        "unit": product.unit,
        "on_hand": product.on_hand,
        "reserved": reserved,
        "available": available,
        "reorder_point": round(rop, 1),
        "order_qty": order_qty,
        "lead_time_days": product.lead_time_days,
        "status": status,
    }


def inventory_rows():
    reserved = reserved_by_product()
    products = Product.query.order_by(Product.sku).all()
    return [inventory_row(p, reserved.get(p.id, 0)) for p in products]