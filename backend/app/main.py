"""App factory: API under /api, frontend as static files at /, one error format."""
import logging

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from .config import Settings, get_settings
from .errors import ApiError, error_response
from .routes import admin, auth, dashboard, profile, tasks

log = logging.getLogger("studyflow")

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"same-origin"),
    (b"x-frame-options", b"DENY"),
    (b"content-security-policy",
     b"default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
     b"font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
     b"connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"),
]


class SecurityHeaders:
    """Pure ASGI middleware that adds security headers to every response."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(SECURITY_HEADERS)
                if scope["path"].startswith("/api"):
                    headers.append((b"cache-control", b"no-store"))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


async def health(request: Request):
    return JSONResponse({"status": "ok"})


async def api_error(request: Request, exc: ApiError):
    return error_response(exc.status, exc.message, exc.fields)


async def http_error(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        message = {404: "Not found.", 405: "Method not allowed."}.get(exc.status_code, exc.detail)
        return error_response(exc.status_code, message)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


async def server_error(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error_response(500, "Something went wrong on our side. Please try again.")


def create_app(settings: Settings | None = None) -> Starlette:
    settings = settings or get_settings()
    api_routes = [Route("/health", health, methods=["GET"]),
                  *auth.routes, *tasks.routes, *dashboard.routes, *profile.routes, *admin.routes]
    app = Starlette(
        routes=[Mount("/api", routes=api_routes),
                Mount("/", app=StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")],
        exception_handlers={ApiError: api_error, HTTPException: http_error, Exception: server_error},
    )
    app.state.settings = settings
    app.add_middleware(SecurityHeaders)
    return app
