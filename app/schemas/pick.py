"""Checks for picks and material requests."""
from app.errors import ApiError
from app.models import Job, Product
from app.schemas.job import whole_number


def clean_pick(data):
    """Returns (job, line, qty) for a valid pick. Raises 422 for bad input,
    404 if the job does not exist."""
    data = data or {}
    problems = {}

    job_number = str(data.get("job_number") or "").strip()
    sku = str(data.get("sku") or "").strip().upper()
    qty = whole_number(data.get("qty"))

    if not job_number:
        problems["job_number"] = "Choose a work order."
    if not sku:
        problems["sku"] = "Enter or scan a product code."
    if qty is None or qty < 1:
        problems["qty"] = "Quantity must be a whole number of 1 or more."
    if problems:
        raise ApiError("Please fix the problems below.", 422, problems)

    job = Job.query.filter_by(job_number=job_number).first()
    if job is None:
        raise ApiError("Job " + job_number + " was not found.", 404)

    line = next((l for l in job.lines if l.product.sku == sku), None)
    if line is None:
        raise ApiError("Please fix the problems below.", 422, {
            "sku": sku + " is not on the BOM for " + job_number
                   + ". Send a material request instead."})
    return job, line, qty


def clean_request(data):
    """Returns (product, qty, note) for a valid material request."""
    data = data or {}
    problems = {}

    sku = str(data.get("sku") or "").strip().upper()
    product = Product.query.filter_by(sku=sku).first() if sku else None
    if product is None:
        problems["sku"] = "Choose an item from the list."

    qty = whole_number(data.get("qty"))
    if qty is None or qty < 1:
        problems["qty"] = "Quantity must be a whole number of 1 or more."

    note = str(data.get("note") or "").strip()
    if len(note) > 120:
        problems["note"] = "Keep the reason under 120 characters."

    if problems:
        raise ApiError("Please fix the problems below.", 422, problems)
    return product, qty, note