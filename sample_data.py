"""Demo data for the StockFlow pages.

Everything is made up. The numbers you see on screen (shortages,
reorder points, suggested order quantities) are calculated by
models/stock_model.py, not typed in.
"""
from datetime import date, timedelta

from models import stock_model as sm

# The current date for the demo.
TODAY = date(2026, 9, 4)

# stock items
# One dictionary per item.
#   on_hand       = quantity on the shelf
#   daily_demand  = average units used per day
#   daily_std     = how much daily demand varies
#   lead_time     = days the supplier takes to deliver
#   annual_demand = units used per year
#   order_cost    = rands to place one order
#   holding_cost  = rands to hold one unit for a year
#   min_order     = smallest quantity the supplier will sell
#   pack          = items are sold in multiples of this
STOCK = {
    "CU-WIND-01": {"desc": "Copper winding wire, 25 kg coil", "bin": "A-01-02", "unit": "coil",
                   "on_hand": 18, "daily_demand": 0.8, "daily_std": 0.5, "lead_time": 14,
                   "annual_demand": 290, "order_cost": 850, "holding_cost": 120, "min_order": 2, "pack": 1},
    "TX-CORE-03": {"desc": "Transformer core, CRGO laminated", "bin": "A-02-01", "unit": "pcs",
                   "on_hand": 4, "daily_demand": 0.25, "daily_std": 0.2, "lead_time": 21,
                   "annual_demand": 90, "order_cost": 1200, "holding_cost": 650, "min_order": 1, "pack": 1},
    "INS-PAPER": {"desc": "Insulating paper roll, 0.13 mm", "bin": "A-03-04", "unit": "roll",
                  "on_hand": 20, "daily_demand": 0.6, "daily_std": 0.4, "lead_time": 10,
                  "annual_demand": 220, "order_cost": 400, "holding_cost": 45, "min_order": 5, "pack": 5},
    "FST-M8": {"desc": "Fastener set M8 (box of 100)", "bin": "B-01-01", "unit": "box",
               "on_hand": 600, "daily_demand": 12, "daily_std": 6, "lead_time": 5,
               "annual_demand": 4300, "order_cost": 150, "holding_cost": 3, "min_order": 50, "pack": 50},
    "PCB-PSU-12": {"desc": "Power supply PCB, 12 V", "bin": "C-02-03", "unit": "pcs",
                   "on_hand": 20, "daily_demand": 1.2, "daily_std": 0.8, "lead_time": 18,
                   "annual_demand": 430, "order_cost": 700, "holding_cost": 95, "min_order": 10, "pack": 10},
    "SM-STL-2MM": {"desc": "Sheet steel 2 mm, 1250x2500", "bin": "D-01-01", "unit": "sheet",
                   "on_hand": 40, "daily_demand": 2.0, "daily_std": 1.2, "lead_time": 7,
                   "annual_demand": 720, "order_cost": 300, "holding_cost": 85, "min_order": 10, "pack": 10},
    "CBL-10MM": {"desc": "Cable 10 mm squared, per metre", "bin": "C-04-02", "unit": "m",
                 "on_hand": 120, "daily_demand": 6, "daily_std": 3, "lead_time": 8,
                 "annual_demand": 2200, "order_cost": 250, "holding_cost": 4, "min_order": 100, "pack": 100},
    "GSKT-EPDM": {"desc": "EPDM gasket strip, per metre", "bin": "B-03-05", "unit": "m",
                  "on_hand": 30, "daily_demand": 1.0, "daily_std": 0.6, "lead_time": 6,
                  "annual_demand": 360, "order_cost": 180, "holding_cost": 6, "min_order": 20, "pack": 20},
}

# job files
# created_days / start_days = days before (-) or after (+) TODAY.
# state: "open" (not started), "kitting" (being picked now), "issued" (done).
JOB_LIST = [
    {"id": "J-2026-0429", "customer": "Highveld Rail Services", "description": "Signalling power supply x4",
     "created_days": -6, "start_days": -1, "state": "issued", "priority": "Normal",
     "bom": {"PCB-PSU-12": 4, "CBL-10MM": 20}},
    {"id": "J-2026-0430", "customer": "Cape Traction Systems", "description": "Auxiliary transformer rework",
     "created_days": -3, "start_days": 0, "state": "kitting", "priority": "Urgent",
     "bom": {"FST-M8": 50, "INS-PAPER": 2, "CBL-10MM": 10}},
    {"id": "J-2026-0431", "customer": "Highveld Rail Services", "description": "500 kVA traction transformer",
     "created_days": 0, "start_days": 1, "state": "open", "priority": "Normal",
     "bom": {"CU-WIND-01": 6, "TX-CORE-03": 1, "INS-PAPER": 4, "FST-M8": 120}},
    {"id": "J-2026-0432", "customer": "Kopano Energy", "description": "24 V DC power cabinets x10",
     "created_days": 0, "start_days": 2, "state": "open", "priority": "Normal",
     "bom": {"PCB-PSU-12": 10, "SM-STL-2MM": 12, "FST-M8": 200, "CBL-10MM": 30}},
    {"id": "J-2026-0433", "customer": "Limpopo Power Co", "description": "Switchgear enclosure",
     "created_days": 0, "start_days": 3, "state": "open", "priority": "Normal",
     "bom": {"SM-STL-2MM": 20, "GSKT-EPDM": 8, "FST-M8": 150}},
    {"id": "J-2026-0434", "customer": "Cape Traction Systems", "description": "Rectifier transformer x2",
     "created_days": -1, "start_days": 5, "state": "open", "priority": "Normal",
     "bom": {"CU-WIND-01": 8, "TX-CORE-03": 2, "INS-PAPER": 6, "CBL-10MM": 40}},
    {"id": "J-2026-0435", "customer": "Highveld Rail Services", "description": "Trackside PSU units",
     "created_days": -1, "start_days": 6, "state": "open", "priority": "Urgent",
     "bom": {"PCB-PSU-12": 15, "CBL-10MM": 25}},
    {"id": "J-2026-0436", "customer": "Kopano Energy", "description": "Substation enclosures x6",
     "created_days": -2, "start_days": 9, "state": "open", "priority": "Normal",
     "bom": {"SM-STL-2MM": 30, "FST-M8": 300, "GSKT-EPDM": 12}},
    {"id": "J-2026-0437", "customer": "Limpopo Power Co", "description": "Distribution transformer",
     "created_days": -2, "start_days": 12, "state": "open", "priority": "Normal",
     "bom": {"CU-WIND-01": 10, "TX-CORE-03": 2}},
]


def build_jobs():
    """Go through the jobs in start-date order and reserve stock for each.

    Returns (jobs, reserved) where reserved is the total quantity of each
    item claimed by all the jobs that are not yet issued.
    """
    on_hand = {}
    for sku in STOCK:
        on_hand[sku] = STOCK[sku]["on_hand"]

    reserved = {}
    jobs = []

    for job_info in sorted(JOB_LIST, key=lambda j: j["start_days"]):
        job = {
            "id": job_info["id"],
            "customer": job_info["customer"],
            "description": job_info["description"],
            "created": TODAY + timedelta(days=job_info["created_days"]),
            "start_date": TODAY + timedelta(days=job_info["start_days"]),
            "days_to_start": job_info["start_days"],
            "priority": job_info["priority"],
            "bom": job_info["bom"],
            "lines": [],
            "shortages": [],
        }

        if job_info["state"] == "issued":
            # Already collected, so it no longer holds any reservation.
            job["status"] = "issued"
        else:
            # Which items are short after what earlier jobs have reserved?
            job["shortages"] = sm.check_job_availability(job_info["bom"], on_hand, reserved)
            short_by = {}
            for s in job["shortages"]:
                short_by[s["sku"]] = s["short_by"]

            # One line per item for the job
            for sku, qty in job_info["bom"].items():
                job["lines"].append({
                    "sku": sku,
                    "desc": STOCK[sku]["desc"],
                    "qty": qty,
                    "free": sm.available_stock(on_hand[sku], reserved.get(sku, 0)),
                    "short_by": short_by.get(sku, 0),
                })

            # Reserve this jobs items so the next job sees less free stock.
            reserved = sm.reserve_job(job_info["bom"], reserved)

            if job_info["state"] == "kitting":
                job["status"] = "kitting"
            elif job["shortages"]:
                job["status"] = "shortage"
            else:
                job["status"] = "reserved"

        jobs.append(job)

    return jobs, reserved


def build_inventory(reserved):
    """One row per stock item, with calculated reorder point and order size."""
    rows = []
    for sku, item in STOCK.items():
        available = sm.available_stock(item["on_hand"], reserved.get(sku, 0))

        buffer = sm.safety_stock(0.95, item["daily_std"], item["lead_time"])
        rop = sm.reorder_point(item["daily_demand"], item["lead_time"], buffer)
        eoq = sm.calculate_eoq(item["annual_demand"], item["order_cost"], item["holding_cost"])
        order_qty = sm.recommended_order_qty(eoq, item["min_order"], item["pack"])

        # Traffic-light status
        if available <= 0.5 * rop:
            status = "critical"
        elif available <= rop:
            status = "low"
        else:
            status = "ok"

        rows.append({
            "sku": sku,
            "desc": item["desc"],
            "bin": item["bin"],
            "unit": item["unit"],
            "on_hand": item["on_hand"],
            "reserved": reserved.get(sku, 0),
            "available": available,
            "rop": round(rop, 1),
            "order_qty": order_qty,
            "lead_time": item["lead_time"],
            "status": status,
        })
    return rows


JOBS, RESERVED = build_jobs()
INVENTORY = build_inventory(RESERVED)


def kpis():
    """The four summary numbers on the dashboard."""
    open_jobs = []
    for job in JOBS:
        if job["status"] != "issued":
            open_jobs.append(job)

    short_items = set()
    for job in open_jobs:
        for s in job["shortages"]:
            short_items.add(s["sku"])

    reserved_lines = 0
    for job in open_jobs:
        reserved_lines += len(job["bom"])

    return {
        "open_jobs": len(open_jobs),
        "shortage_items": len(short_items),
        "reserved_lines": reserved_lines,
        "upcoming": len(sm.jobs_in_window(open_jobs, TODAY, 7)),
    }


def js_payload():
    """The data handed to the browser's JavaScript (window.SF in base.html)."""
    stock = {}
    for row in INVENTORY:
        stock[row["sku"]] = {
            "desc": row["desc"], "bin": row["bin"], "unit": row["unit"],
            "available": row["available"], "onHand": row["on_hand"],
        }

    jobs = {}
    for job in JOBS:
        lines = job["lines"]
        if not lines:
            # Issued jobs have no stock check, show the plain materials list.
            for sku, qty in job["bom"].items():
                lines.append({"sku": sku, "desc": STOCK[sku]["desc"], "qty": qty,
                              "free": None, "short_by": 0})
        jobs[job["id"]] = {
            "customer": job["customer"], "description": job["description"],
            "start": job["start_date"].isoformat(), "status": job["status"],
            "lines": lines,
        }

    return {"today": TODAY.isoformat(), "stock": stock, "jobs": jobs}