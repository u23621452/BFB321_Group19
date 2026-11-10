"""Recording a pick: stock goes out, the ledger gets a row, the job moves on."""
from app.errors import ApiError
from app.extensions import db
from app.models import StockMovement
from app.services.jobs import refresh_statuses


def record_pick(job, line, qty, user):
    product = line.product

    if job.status == "issued":
        raise ApiError(job.job_number + " has already been fully issued.", 409)

    remaining = line.qty - line.picked_qty
    if qty > remaining:
        raise ApiError("Only {} more {} needed for {}.".format(
            remaining, product.sku, job.job_number), 409)
    if qty > product.on_hand:
        raise ApiError("Only {} {} on hand for {}.".format(
            product.on_hand, product.unit, product.sku), 409)

    line.picked_qty += qty
    product.on_hand -= qty
    db.session.add(StockMovement(product=product, job_id=job.id,
                                 user_id=user.id, qty=-qty, kind="pick"))

    # a job is "issued" once every BOM line is fully picked, otherwise "kitting"
    if all(l.picked_qty >= l.qty for l in job.lines):
        job.status = "issued"
    else:
        job.status = "kitting"

    db.session.flush()
    refresh_statuses()
    db.session.commit()

    return {
        "job_number": job.job_number,
        "sku": product.sku,
        "picked": qty,
        "picked_total": line.picked_qty,
        "remaining": line.qty - line.picked_qty,
        "on_hand_after": product.on_hand,
        "job_status": job.status,
    }