from flask import Blueprint, request, jsonify

from app.errors import ApiError
from app.services import stock
from app.utils import role_required, get_page_params, paginate_list

bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

VALID_STATUSES = ("ok", "low", "critical")


@bp.get("")
@role_required("reception", "storeroom", "operator")
def list_inventory():
    """GET /api/inventory?page=1&per_page=10&status=low&search=cu"""
    page, per_page = get_page_params()
    rows = stock.inventory_rows()

    status = request.args.get("status")
    if status:
        if status not in VALID_STATUSES:
            raise ApiError("status must be ok, low or critical.", 400)
        rows = [r for r in rows if r["status"] == status]

    search = (request.args.get("search") or "").strip().lower()
    if search:
        rows = [r for r in rows
                if search in r["sku"].lower() or search in r["description"].lower()]

    return jsonify(paginate_list(rows, page, per_page))