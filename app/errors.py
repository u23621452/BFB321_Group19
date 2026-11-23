"""One place that turns every error into the same JSON shape:
{"error": {"code": 404, "message": "..."}}
"""
from flask import jsonify, current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from app.extensions import db


class ApiError(Exception):
    """Raise this anywhere in the API to send a clean error to the browser."""

    def __init__(self, message, status=400, details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.details = details


def error_response(message, status, details=None):
    body = {"error": {"code": status, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        # undo anything half-written before the problem was found
        db.session.rollback()
        return error_response(err.message, err.status, err.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return error_response(err.description, err.code)

    @app.errorhandler(IntegrityError)
    def handle_conflict(err):
        # a unique or foreign key rule in the database was broken
        db.session.rollback()
        current_app.logger.warning("Database conflict: %s", err.orig)
        return error_response("That conflicts with data that already exists.", 409)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # a failed write must not leave the session half-finished
        db.session.rollback()
        # log the full problem for us, show the user something short
        current_app.logger.exception("Unhandled error: %s", err)
        return error_response("Something went wrong on the server.", 500)