"""One place that turns every error into the same JSON shape:
{"error": {"code": 404, "message": "..."}}
"""
from flask import jsonify, current_app
from werkzeug.exceptions import HTTPException


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
        return error_response(err.message, err.status, err.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return error_response(err.description, err.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        # log the full problem for us, show the user something short
        current_app.logger.exception("Unhandled error: %s", err)
        return error_response("Something went wrong on the server.", 500)