from typing import Dict, Any
from ..types import CreateUserPayload, UpdateUserPayload
from ..normalize import strip_plus_tag

def _normalize_email_in_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(data) if data is not None else {}
    email = payload.get("email")
    if isinstance(email, str) and email:
        payload["email"] = strip_plus_tag(email)
    return payload

class UsersResource:
    def __init__(self, client: "SolidarityClient"):
        self._client = client

    def create_or_update(self, payload: CreateUserPayload) -> Dict[str, Any]:
        if not (payload.get("phone_number") or payload.get("email")):
            raise ValueError("Either phone_number or email is required")
        payload = _normalize_email_in_payload(payload)
        return self._client.request("POST", "/v1/users", json=payload)

    def update(self, user_id: int, payload: UpdateUserPayload) -> Dict[str, Any]:
        payload = _normalize_email_in_payload(payload)
        return self._client.request("PUT", f"/v1/users/{int(user_id)}", json=payload)

    def get(self, user_id: int) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/users/{int(user_id)}")