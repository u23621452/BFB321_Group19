from datetime import date

from flask import Blueprint, jsonify

from app.models import Job, MaterialRequest, StockMovement
from app.services import jobs as job_service
from app.services import stock
from app.utils import role_required
from models import stock_model as sm

bp = Blueprint("kpis", __name__, url_prefix="/api/kpis")


@bp.get("")
@role_required("reception", "storeroom", "operator")
def kpis():
    """GET /api/kpis - the numbers shown on the dashboard tiles."""
    today = date.today()
    open_jobs = Job.query.filter(Job.status.in_(stock.ACTIVE_STATUSES)).all()
    shortages = job_service.shortages_by_job()

    short_skus = {s["sku"] for lst in shortages.values() for s in lst}
    next_7_days = sm.jobs_in_window(
        [{"start_date": j.start_date} for j in open_jobs], today, 7)

    inventory = stock.inventory_rows()
    picks_today = [m for m in StockMovement.query.filter_by(kind="pick").all()
                   if m.created_at.date() == today]

    return jsonify({
        "open_jobs": len(open_jobs),
        "shortage_jobs": sum(1 for j in open_jobs if j.status == "shortage"),
        "shortage_items": len(short_skus),
        "reserved_lines": sum(len(j.lines) for j in open_jobs),
        "upcoming_7_days": len(next_7_days),
        "critical_items": sum(1 for r in inventory if r["status"] == "critical"),
        "low_items": sum(1 for r in inventory if r["status"] == "low"),
        "open_requests": MaterialRequest.query.filter_by(status="open").count(),
        "picks_today": len(picks_today),
    })