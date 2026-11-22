"""One error format for every failure.

v1 had a `DbConnectionError` for every database problem (even bad input),
returned `str(err)` to the client (leaking host names and SQL details), and
still served Flask's HTML pages for errors it had no handler for, such as 415.

Every error here is JSON shaped as:
    {"error": {"code": "...", "message": "...", "details": [...]}}
Unexpected exceptions are logged in full server-side and the client gets a
generic message.
"""

from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: list | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details


class NotFound(ApiError):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(404, "not_found", f"{resource} {resource_id} does not exist")


class Conflict(ApiError):
    def __init__(self, message: str):
        super().__init__(409, "conflict", message)


def _body(code: str, message: str, details: list | None = None):
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return jsonify({"error": error})


def register(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def _api_error(e: ApiError):
        return _body(e.code, e.message, e.details), e.status

    @app.errorhandler(ValidationError)
    def _validation_error(e: ValidationError):
        details = [
            {"field": ".".join(str(p) for p in err["loc"]) or None, "message": err["msg"]}
            for err in e.errors(include_url=False)
        ]
        return _body("validation_error", "Request body failed validation", details), 422

    @app.errorhandler(HTTPException)
    def _http_error(e: HTTPException):
        code = (e.name or "error").lower().replace(" ", "_")
        return _body(code, e.description or e.name), e.code

    @app.errorhandler(Exception)
    def _unexpected(e: Exception):
        app.logger.exception("Unhandled error")
        return _body("internal_error", "Something went wrong on our side"), 500
