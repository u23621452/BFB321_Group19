from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.schemas.pick import clean_pick
from app.services.picks import record_pick
from app.utils import role_required

bp = Blueprint("picks", __name__, url_prefix="/api/picks")


@bp.post("")
@role_required("operator", "storeroom")
def confirm_pick():
    """POST /api/picks  {job_number, sku, qty} - the operator confirms a pick."""
    job, line, qty = clean_pick(request.get_json(silent=True))
    result = record_pick(job, line, qty, current_user)
    return jsonify(result), 201