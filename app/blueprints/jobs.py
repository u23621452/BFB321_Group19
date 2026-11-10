from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.errors import ApiError
from app.models import Job
from app.models.job import JOB_STATUSES
from app.schemas.job import clean_job
from app.services import jobs as job_service
from app.utils import role_required, get_page_params, paginate_query

bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


@bp.get("")
@role_required("reception", "storeroom", "operator")
def list_jobs():
    """GET /api/jobs?page=1&per_page=10&status=shortage&search=kopano"""
    page, per_page = get_page_params()
    query = Job.query

    status = request.args.get("status")
    if status:
        if status not in JOB_STATUSES:
            raise ApiError("status must be one of: " + ", ".join(JOB_STATUSES), 400)
        query = query.filter(Job.status == status)

    # ?open=1 hides jobs that have already been fully issued
    if request.args.get("open") == "1":
        query = query.filter(Job.status != "issued")
    search = (request.args.get("search") or "").strip()
    if search:
        like = "%" + search + "%"
        query = query.filter(Job.job_number.ilike(like)
                             | Job.customer.ilike(like)
                             | Job.description.ilike(like))

    query = query.order_by(Job.start_date, Job.id)
    return jsonify(paginate_query(
        query, page, per_page,
        lambda job: job_service.job_to_dict(job, with_lines=False)))


@bp.get("/<job_number>")
@role_required("reception", "storeroom", "operator")
def get_job(job_number):
    job = Job.query.filter_by(job_number=job_number).first()
    if job is None:
        raise ApiError("Job " + job_number + " was not found.", 404)
    shortages = job_service.shortages_by_job().get(job.id, [])
    return jsonify(job_service.job_to_dict(job, shortages))


@bp.post("")
@role_required("reception")
def create_job():
    """POST /api/jobs  - open a job file and soft-reserve its stock."""
    clean = clean_job(request.get_json(silent=True))
    job = job_service.create_job(clean, current_user)
    shortages = job_service.shortages_by_job().get(job.id, [])
    return jsonify(job_service.job_to_dict(job, shortages)), 201