from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.errors import ApiError
from app.extensions import db
from app.models import MaterialRequest
from app.schemas.pick import clean_request
from app.utils import role_required, get_page_params, paginate_query

bp = Blueprint("material_requests", __name__, url_prefix="/api/requests")


def request_to_dict(row):
    return {
        "id": row.id,
        "sku": row.product.sku,
        "description": row.product.description,
        "qty": row.qty,
        "note": row.note,
        "status": row.status,
        "created_at": row.created_at.isoformat(),
    }


@bp.post("")
@role_required("operator", "storeroom")
def create_request():
    """POST /api/requests  {sku, qty, note} - an operator asks for more material."""
    product, qty, note = clean_request(request.get_json(silent=True))
    row = MaterialRequest(product=product, qty=qty, note=note or None,
                          requested_by=current_user.id)
    db.session.add(row)
    db.session.commit()
    return jsonify(request_to_dict(row)), 201


@bp.get("")
@role_required("storeroom")
def list_requests():
    """GET /api/requests?status=open&page=1"""
    page, per_page = get_page_params()
    query = MaterialRequest.query

    status = request.args.get("status")
    if status:
        if status not in ("open", "done"):
            raise ApiError("status must be open or done.", 400)
        query = query.filter(MaterialRequest.status == status)

    query = query.order_by(MaterialRequest.created_at.desc())
    return jsonify(paginate_query(query, page, per_page, request_to_dict))