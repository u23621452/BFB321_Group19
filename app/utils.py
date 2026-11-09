from functools import wraps

from flask import request
from flask_login import current_user

from app.errors import ApiError


def role_required(*roles):
    """Only let logged-in users with one of these roles through.
    Admins are always allowed."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                raise ApiError("Please log in first.", 401)
            if current_user.role != "admin" and current_user.role not in roles:
                raise ApiError("You do not have permission to do this.", 403)
            return view(*args, **kwargs)
        return wrapper
    return decorator


def get_page_params():
    """Read ?page= and ?per_page= from the URL, with safe limits."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
    except ValueError:
        raise ApiError("page and per_page must be whole numbers.", 400)
    if page < 1 or per_page < 1:
        raise ApiError("page and per_page must be 1 or more.", 400)
    return page, min(per_page, 100)


def paginate_list(items, page, per_page):
    """Cut a Python list into one page and describe the paging."""
    total = len(items)
    start = (page - 1) * per_page
    return {
        "items": items[start:start + per_page],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": max((total + per_page - 1) // per_page, 1),
    }


def paginate_query(query, page, per_page, convert):
    """Run a database query one page at a time. `convert` turns each row
    into the dictionary we send back."""
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [convert(row) for row in result.items],
        "page": page,
        "per_page": per_page,
        "total": result.total,
        "pages": max(result.pages, 1),
    }