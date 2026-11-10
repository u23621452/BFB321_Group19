"""The storeroom's advance planning queue."""
from datetime import date, timedelta

from app.models import Job, Product
from app.services import jobs as job_service
from app.services import stock
from models import stock_model as sm


def build_queue(days):
    today = date.today()
    open_jobs = Job.query.filter(Job.status.in_(stock.ACTIVE_STATUSES)).all()

    # the supply chain model picks out the jobs that start inside the window
    candidates = [{"start_date": job.start_date, "job": job} for job in open_jobs]
    in_window = sm.jobs_in_window(candidates, today, days)

    all_shortages = job_service.shortages_by_job()
    jobs = []
    for item in in_window:
        job = item["job"]
        jobs.append(job_service.job_to_dict(job, all_shortages.get(job.id, [])))

    return {
        "window_days": days,
        "from": today.isoformat(),
        "to": (today + timedelta(days=days)).isoformat(),
        "jobs": jobs,
        "shortage_summary": shortage_summary(jobs, today),
    }


def shortage_summary(jobs, today):
    """Adds up the shortages across the jobs in the window, per product, and
    works out when each one has to be ordered to arrive in time."""
    totals = {}
    for job in jobs:
        for s in job["shortages"]:
            row = totals.setdefault(s["sku"], {
                "sku": s["sku"], "description": s["description"],
                "short_by": 0, "needed_by": job["start_date"], "jobs": []})
            row["short_by"] += s["short_by"]
            row["needed_by"] = min(row["needed_by"], job["start_date"])
            row["jobs"].append(job["job_number"])

    reserved = stock.reserved_by_product()
    products = {p.sku: p for p in Product.query.filter(Product.sku.in_(totals)).all()}

    summary = []
    for sku, row in totals.items():
        product = products[sku]
        info = stock.inventory_row(product, reserved.get(product.id, 0))
        needed_by = date.fromisoformat(row["needed_by"])
        order_by = needed_by - timedelta(days=product.lead_time_days)
        row["recommended_order_qty"] = info["order_qty"]
        row["lead_time_days"] = product.lead_time_days
        row["order_by"] = order_by.isoformat()
        # if the order date has already passed, normal delivery is too slow
        row["expedite"] = order_by < today
        summary.append(row)

    summary.sort(key=lambda r: (r["order_by"], r["sku"]))
    return summary