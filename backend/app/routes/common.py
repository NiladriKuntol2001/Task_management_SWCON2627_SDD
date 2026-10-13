"""Small helpers shared by route modules."""
import json

from starlette.requests import Request

from ..errors import ApiError


async def json_body(request: Request) -> dict:
    raw = await request.body()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise ApiError(400, "The request body must be valid JSON.")
    if not isinstance(data, dict):
        raise ApiError(400, "The request body must be a JSON object.")
    return data


def db_path(request: Request) -> str:
    return request.app.state.settings.db_path
