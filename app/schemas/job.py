"""Checks the data sent when a new job is created."""
from datetime import date

from app.errors import ApiError
from app.models import Product

PRIORITIES = ("Normal", "Urgent")


def whole_number(value):
    """Return value as an int, or None if it is not a whole number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def clean_job(data):
    """Check the request and return tidy values. Raises a 422 error that lists
    every problem found, so the form can show them all at once."""
    data = data or {}
    problems = {}

    customer = str(data.get("customer") or "").strip()
    if not 3 <= len(customer) <= 80:
        problems["customer"] = "Customer must be 3 to 80 characters."

    description = str(data.get("description") or "").strip()
    if not 1 <= len(description) <= 100:
        problems["description"] = "Description must be 1 to 100 characters."

    start_date = None
    try:
        start_date = date.fromisoformat(str(data.get("start_date") or ""))
        if start_date < date.today():
            problems["start_date"] = "Start date cannot be in the past."
    except ValueError:
        problems["start_date"] = "Use the date format YYYY-MM-DD."

    priority = data.get("priority") or "Normal"
    if priority not in PRIORITIES:
        problems["priority"] = "Priority must be Normal or Urgent."

    lines = []
    raw_lines = data.get("lines")
    if not isinstance(raw_lines, list) or not raw_lines:
        problems["lines"] = "Add at least one BOM line."
    else:
        skus = [str(l.get("sku", "")).strip().upper() if isinstance(l, dict) else ""
                for l in raw_lines]
        found = {p.sku: p for p in Product.query.filter(Product.sku.in_(skus)).all()}
        seen = set()
        for sku, line in zip(skus, raw_lines):
            qty = whole_number(line.get("qty")) if isinstance(line, dict) else None
            if sku not in found:
                problems["lines"] = "Unknown product code: " + (sku or "(blank)")
            elif sku in seen:
                problems["lines"] = "Each product can only appear once: " + sku
            elif qty is None or qty < 1:
                problems["lines"] = "Quantity must be a whole number of 1 or more (" + sku + ")."
            else:
                lines.append((found[sku], qty))
            seen.add(sku)

    if problems:
        raise ApiError("Please fix the problems below.", 422, problems)

    return {"customer": customer, "description": description,
            "start_date": start_date, "priority": priority, "lines": lines}