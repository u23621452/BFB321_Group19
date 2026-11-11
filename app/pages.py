"""The web pages. Each page is a thin HTML shell - the data is loaded by
JavaScript from the /api/... endpoints."""
from datetime import date
from functools import wraps

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

bp = Blueprint("pages", __name__)

# endpoint, label, icon, roles that may open it (admin may open everything)
PAGES = [
    ("pages.dashboard", "Dashboard", "house-door", ("reception", "storeroom", "operator")),
    ("pages.job_files", "Job files", "journal-text", ("reception",)),
    ("pages.queue", "Storeroom queue", "clock-history", ("storeroom", "reception")),
]


def can_open(role, roles):
    return role == "admin" or role in roles


def page_access(*roles):
    """Send visitors to the login page, and send people without permission
    back to the dashboard."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("pages.login_page"))
            if not can_open(current_user.role, roles):
                return redirect(url_for("pages.dashboard"))
            return view(*args, **kwargs)
        return wrapper
    return decorator


@bp.app_context_processor
def add_page_info():
    """Makes the menu items and today's date available in every template."""
    items = []
    if current_user.is_authenticated:
        items = [(endpoint, label, icon) for endpoint, label, icon, roles in PAGES
                 if can_open(current_user.role, roles)]
    return {"nav_items": items, "active_endpoint": request.endpoint,
            "today": date.today()}


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("pages.dashboard"))
    return redirect(url_for("pages.login_page"))


@bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("pages.dashboard"))
    return render_template("login.html")


@bp.get("/dashboard")
@page_access("reception", "storeroom", "operator")
def dashboard():
    return render_template("dashboard.html")


@bp.get("/jobs")
@page_access("reception")
def job_files():
    return render_template("job_files.html")


@bp.get("/queue")
@page_access("storeroom", "reception")
def queue():
    return render_template("queue.html")