"""Job logic that needs the database: shortages, statuses, creating jobs."""
import re
from datetime import date

from app.extensions import db
from app.models import Product, Job, JobLine
from app.services.stock import ACTIVE_STATUSES
from models import stock_model as sm


def shortages_by_job():
    """Work through the open jobs in start-date order. Each job takes what it
    needs from the free stock; whatever is left over goes to the next job.

    Returns {job.id: [shortage, ...]} - an empty list means fully covered."""
    products = {p.id: p for p in Product.query.all()}
    jobs = (Job.query.filter(Job.status.in_(ACTIVE_STATUSES))
            .order_by(Job.start_date, Job.id).all())

    promised = {}      # {product_id: units already given to earlier jobs}
    result = {}
    for job in jobs:
        shortages = []
        for line in job.lines:
            product = products[line.product_id]
            needed = line.qty - line.picked_qty
            free = sm.available_stock(product.on_hand, promised.get(product.id, 0))
            if needed > free:
                shortages.append({
                    "sku": product.sku,
                    "description": product.description,
                    "required": needed,
                    "free": free,
                    "short_by": needed - free,
                })
            promised[product.id] = promised.get(product.id, 0) + needed
        result[job.id] = shortages
    return result


def refresh_statuses():
    """Re-check every job that is waiting (not kitting or issued yet)."""
    shortages = shortages_by_job()
    waiting = Job.query.filter(Job.status.in_(("reserved", "shortage"))).all()
    for job in waiting:
        job.status = "shortage" if shortages.get(job.id) else "reserved"


def next_job_number():
    numbers = [int(re.search(r"(\d+)$", n).group(1))
               for (n,) in db.session.query(Job.job_number).all()]
    return "J-{}-{:04d}".format(date.today().year, max(numbers, default=0) + 1)


def create_job(clean, user):
    """Save a validated job, reserve its stock and set its status."""
    job = Job(job_number=next_job_number(), customer=clean["customer"],
              description=clean["description"], start_date=clean["start_date"],
              priority=clean["priority"], created_by=user.id)
    for product, qty in clean["lines"]:
        job.lines.append(JobLine(product=product, qty=qty))
    db.session.add(job)
    db.session.flush()          # gives the job an id without saving for good
    refresh_statuses()
    db.session.commit()
    return job


def job_to_dict(job, shortages=None, with_lines=True):
    """Turn a job into the dictionary we send to the browser."""
    shortages = shortages or []
    short_by_sku = {s["sku"]: s["short_by"] for s in shortages}
    data = {
        "job_number": job.job_number,
        "customer": job.customer,
        "description": job.description,
        "start_date": job.start_date.isoformat(),
        "days_to_start": (job.start_date - date.today()).days,
        "priority": job.priority,
        "status": job.status,
        "line_count": len(job.lines),
    }
    if with_lines:
        data["lines"] = [{
            "sku": line.product.sku,
            "description": line.product.description,
            "qty": line.qty,
            "picked_qty": line.picked_qty,
            "short_by": short_by_sku.get(line.product.sku, 0),
        } for line in job.lines]
        data["shortages"] = shortages
    return data