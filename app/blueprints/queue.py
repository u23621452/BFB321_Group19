from flask import Blueprint, request, jsonify

from app.errors import ApiError
from app.services.queue import build_queue
from app.utils import role_required

bp = Blueprint("queue", __name__, url_prefix="/api/queue")


@bp.get("")
@role_required("storeroom", "reception")
def storeroom_queue():
    """GET /api/queue?days=7  - jobs starting soon, with shortage alerts."""
    try:
        days = int(request.args.get("days", 7))
    except ValueError:
        raise ApiError("days must be a whole number.", 400)
    if not 1 <= days <= 30:
        raise ApiError("days must be between 1 and 30.", 400)
    return jsonify(build_queue(days))