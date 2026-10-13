"""One error shape for the whole API: {"error": {"message": ..., "fields": {...}}}."""
from starlette.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status: int, message: str, fields: dict[str, str] | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.fields = fields or {}


def not_found(what: str = "Task") -> ApiError:
    return ApiError(404, f"{what} not found.")


def error_response(status: int, message: str, fields: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"error": {"message": message, "fields": fields or {}}}, status_code=status)
