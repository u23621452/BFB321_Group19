"""Fills the database with demo data.  Run with:  python seed.py

All names and numbers are made up for the demo. Running it again wipes the
old demo data first, so it is safe to repeat.
"""
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import (User, Product, Job, JobLine,
                        StockMovement, MaterialRequest)
from models import stock_model as sm

# sku: description, bin, unit, on_hand, daily_demand, daily_std, lead_time,
#      annual_demand, order_cost (R), holding_cost (R per unit per year),
#      min_order, pack_size, unit_cost (R)
PRODUCTS = {
    "CU-WIND-01": ("Copper winding wire, 25 kg coil", "A-01-02", "coil", 18, 0.8, 0.5, 14, 290, 850, 120, 2, 1, 2400),
    "TX-CORE-03": ("Transformer core, CRGO laminated", "A-02-01", "pcs", 4, 0.25, 0.2, 21, 90, 1200, 650, 1, 1, 13000),
    "INS-PAPER": ("Insulating paper roll, 0.13 mm", "A-03-04", "roll", 20, 0.6, 0.4, 10, 220, 400, 45, 5, 5, 900),
    "FST-M8": ("Fastener set M8 (box of 100)", "B-01-01", "box", 600, 12, 6, 5, 4300, 150, 3, 50, 50, 60),
    "PCB-PSU-12": ("Power supply PCB, 12 V", "C-02-03", "pcs", 20, 1.2, 0.8, 18, 430, 700, 95, 10, 10, 1900),
    "SM-STL-2MM": ("Sheet steel 2 mm, 1250x2500", "D-01-01", "sheet", 40, 2.0, 1.2, 7, 720, 300, 85, 10, 10, 1700),
    "CBL-10MM": ("Cable 10 mm2, per metre", "C-04-02", "m", 120, 6, 3, 8, 2200, 250, 4, 100, 100, 80),
    "GSKT-EPDM": ("EPDM gasket strip, per metre", "B-03-05", "m", 30, 1.0, 0.6, 6, 360, 180, 6, 20, 20, 120),
}

# job number, customer, description, start (days from today), priority, state, BOM
JOBS = [
    ("J-2026-0429", "Highveld Rail Services", "Signalling power supply x4", -1, "Normal", "issued",
     {"PCB-PSU-12": 4, "CBL-10MM": 20}),
    ("J-2026-0430", "Cape Traction Systems", "Auxiliary transformer rework", 0, "Urgent", "kitting",
     {"FST-M8": 50, "INS-PAPER": 2, "CBL-10MM": 10}),
    ("J-2026-0431", "Highveld Rail Services", "500 kVA traction transformer", 1, "Normal", "open",
     {"CU-WIND-01": 6, "TX-CORE-03": 1, "INS-PAPER": 4, "FST-M8": 120}),
    ("J-2026-0432", "Kopano Energy", "24 V DC power cabinets x10", 2, "Normal", "open",
     {"PCB-PSU-12": 10, "SM-STL-2MM": 12, "FST-M8": 200, "CBL-10MM": 30}),
    ("J-2026-0433", "Limpopo Power Co", "Switchgear enclosure", 3, "Normal", "open",
     {"SM-STL-2MM": 20, "GSKT-EPDM": 8, "FST-M8": 150}),
    ("J-2026-0434", "Cape Traction Systems", "Rectifier transformer x2", 5, "Normal", "open",
     {"CU-WIND-01": 8, "TX-CORE-03": 2, "INS-PAPER": 6, "CBL-10MM": 40}),
    ("J-2026-0435", "Highveld Rail Services", "Trackside PSU units", 6, "Urgent", "open",
     {"PCB-PSU-12": 15, "CBL-10MM": 25}),
    ("J-2026-0436", "Kopano Energy", "Substation enclosures x6", 9, "Normal", "open",
     {"SM-STL-2MM": 30, "FST-M8": 300, "GSKT-EPDM": 12}),
    ("J-2026-0437", "Limpopo Power Co", "Distribution transformer", 12, "Normal", "open",
     {"CU-WIND-01": 10, "TX-CORE-03": 2}),
]

USERS = [
    ("Rita Reception", "reception@stockflow.test", "reception"),
    ("Sam Storeroom", "storeroom@stockflow.test", "storeroom"),
    ("Olivia Operator", "operator@stockflow.test", "operator"),
    ("Admin User", "admin@stockflow.test", "admin"),
]
DEMO_PASSWORD = "Password123"   # demo logins only


def wipe_old_data():
    for table in (StockMovement, MaterialRequest, JobLine, Job, Product, User):
        db.session.query(table).delete()
    db.session.commit()


def add_users():
    users = {}
    for name, email, role in USERS:
        user = User(name=name, email=email, role=role)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        users[role] = user
    db.session.commit()
    return users


def add_products():
    products = {}
    for sku, d in PRODUCTS.items():
        (desc, bin_, unit, on_hand, daily, daily_std, lead, annual,
         order_cost, holding, moq, pack, cost) = d
        products[sku] = Product(
            sku=sku, description=desc, bin_location=bin_, unit=unit,
            on_hand=on_hand, daily_demand=daily, daily_demand_std=daily_std,
            lead_time_days=lead, annual_demand=annual, order_cost=order_cost,
            holding_cost=holding, min_order_qty=moq, pack_size=pack,
            unit_cost=cost)
        db.session.add(products[sku])
    db.session.commit()
    return products


def add_jobs(products, reception_user):
    today = date.today()
    on_hand = {sku: p.on_hand for sku, p in products.items()}
    reserved = {}          # running total of stock already promised to jobs

    for number, customer, desc, offset, priority, state, bom in JOBS:
        job = Job(job_number=number, customer=customer, description=desc,
                  start_date=today + timedelta(days=offset), priority=priority,
                  created_by=reception_user.id)

        if state == "issued":
            job.status = "issued"
        else:
            # same check the API will use when a job is created
            shortages = sm.check_job_availability(bom, on_hand, reserved)
            reserved = sm.reserve_job(bom, reserved)
            if state == "kitting":
                job.status = "kitting"
            else:
                job.status = "shortage" if shortages else "reserved"

        for sku, qty in bom.items():
            picked = qty if state == "issued" else 0
            job.lines.append(JobLine(product=products[sku], qty=qty, picked_qty=picked))
        db.session.add(job)
    db.session.commit()


def run():
    app = create_app()
    with app.app_context():
        db.create_all()          # only creates tables that are missing
        wipe_old_data()
        users = add_users()
        products = add_products()
        add_jobs(products, users["reception"])
        print("Seeded:", Product.query.count(), "products,",
              Job.query.count(), "jobs,", JobLine.query.count(), "job lines,",
              User.query.count(), "users")


if __name__ == "__main__":
    run()