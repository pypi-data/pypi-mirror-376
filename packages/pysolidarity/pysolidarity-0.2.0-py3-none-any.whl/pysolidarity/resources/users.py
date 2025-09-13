from typing import Dict, Any, Optional
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

    def enroll_in_automation(
        self,
        automation_id: int,
        *,
        user_id: Optional[int] = None,
        hash_id: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        POST /v1/automation_enrollments
        Enroll a user in an automation by one of: user_id, hash_id, phone_number, or email.
        Email is normalized to strip +tags.
        """
        if automation_id is None:
            raise ValueError("automation_id is required")
        if not any([user_id, hash_id, phone_number, email]):
            raise ValueError("Provide at least one identifier: user_id, hash_id, phone_number, or email")

        payload: Dict[str, Any] = {"automation_id": int(automation_id)}
        if user_id is not None:
            payload["user_id"] = int(user_id)
        if hash_id:
            payload["hash_id"] = hash_id
        if phone_number:
            payload["phone_number"] = phone_number
        if email:
            payload["email"] = strip_plus_tag(email)

        return self._client.request("POST", "/v1/automation_enrollments", json=payload)
