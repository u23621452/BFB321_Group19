from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app.errors import ApiError
from app.models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def user_json(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        raise ApiError("Email and password are required.", 400)

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        raise ApiError("Wrong email or password.", 401)

    login_user(user)
    return jsonify(user_json(user))


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out."})


@bp.get("/me")
@login_required
def me():
    return jsonify(user_json(current_user))