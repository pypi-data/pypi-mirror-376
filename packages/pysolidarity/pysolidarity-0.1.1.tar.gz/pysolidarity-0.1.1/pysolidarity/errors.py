from typing import Any, Optional
import json
import requests

class SolidarityError(Exception):
    """Base exception for this SDK."""

class HTTPError(SolidarityError):
    def __init__(self, message: str, *, status_code: int, payload: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload

class NotFound(HTTPError):
    pass

class ValidationError(HTTPError):
    pass

class Unauthorized(HTTPError):
    pass

class RateLimited(HTTPError):
    pass

class ServerError(HTTPError):
    pass


def _safe_json(resp: requests.Response):
    try:
        return resp.json()
    except Exception:
        try:
            return json.loads(resp.text)
        except Exception:
            return None


def raise_for_status(resp: requests.Response) -> None:
    if 200 <= resp.status_code < 300:
        return

    payload = _safe_json(resp)
    msg = None
    if isinstance(payload, dict):
        msg = payload.get("error") or payload.get("message")
    msg = msg or f"HTTP {resp.status_code}: {resp.text[:300]}"

    if resp.status_code == 401:
        raise Unauthorized(msg, status_code=resp.status_code, payload=payload)
    if resp.status_code == 404:
        raise NotFound(msg, status_code=resp.status_code, payload=payload)
    if resp.status_code == 422:
        raise ValidationError(msg, status_code=resp.status_code, payload=payload)
    if resp.status_code == 429:
        raise RateLimited(msg, status_code=resp.status_code, payload=payload)
    if resp.status_code >= 500:
        raise ServerError(msg, status_code=resp.status_code, payload=payload)

    raise HTTPError(msg, status_code=resp.status_code, payload=payload)