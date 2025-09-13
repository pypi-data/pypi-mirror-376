from typing import Dict, Any
from ..types import CreateUserPayload, UpdateUserPayload

class UsersResource:
    def __init__(self, client: "SolidarityClient"):
        self._client = client

    def create_or_update(self, payload: CreateUserPayload) -> Dict[str, Any]:
        if not (payload.get("phone_number") or payload.get("email")):
            raise ValueError("Either phone_number or email is required")
        return self._client.request("POST", "/v1/users", json=dict(payload))

    def update(self, user_id: int, payload: UpdateUserPayload) -> Dict[str, Any]:
        return self._client.request("PUT", f"/v1/users/{int(user_id)}", json=dict(payload))

    def get(self, user_id: int) -> Dict[str, Any]:
        return self._client.request("GET", f"/v1/users/{int(user_id)}")