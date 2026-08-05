"""Thin, centralized REST/SSE client for the RAG Video Insight API."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Iterator

import requests


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class APIClient:
    base_url: str = os.getenv("API_BASE_URL", "http://localhost:3333/api/v1")
    token: str | None = None
    timeout: int = 30

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    @property
    def endpoint(self) -> str:
        return self.base_url.rstrip("/")

    @staticmethod
    def _unwrap(data: Any) -> Any:
        # Supports common NestJS response envelopes while keeping the UI decoupled.
        if isinstance(data, dict) and isinstance(data.get("data"), (dict, list)):
            return data["data"]
        return data

    @staticmethod
    def _message(response: requests.Response) -> str:
        try:
            body = response.json()
            value = (
                body.get("message", body.get("error", "Request failed"))
                if isinstance(body, dict)
                else "Request failed"
            )
            return ", ".join(value) if isinstance(value, list) else str(value)
        except ValueError:
            return response.text or "Request failed"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.endpoint}{path}",
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise APIError(f"Could not reach the API: {exc}") from exc
        if not response.ok:
            raise APIError(self._message(response), response.status_code)
        if response.status_code == 204 or not response.content:
            return {}
        try:
            return self._unwrap(response.json())
        except ValueError as exc:
            raise APIError(
                "The API returned an invalid JSON response.", response.status_code
            ) from exc

    @staticmethod
    def as_list(payload: Any, *keys: str) -> list[dict[str, Any]]:
        """Normalize collection DTOs without leaking envelope details into views."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in keys or ("items", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    # /--------- Auth endpoints ---------/
    def register(self, name: str, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/register",
            json={"name": name, "email": email, "password": password},
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password, "rememberMe": True},
        )

    def get_user_profile(self) -> dict[str, Any]:
        return self._request("GET", "/auth/profile")

    def update_user_profile(
        self,
        user_id: str,
        name: str | None = None,
        email: str | None = None,
        profileImage: str | None = None,
        verifyToken: str | None = None,
    ) -> dict[str, Any]:
        payload = {}
        if name is not None:
            payload["name"] = name
        if email is not None:
            payload["email"] = email
        if profileImage is not None:
            payload["profileImage"] = profileImage
        if verifyToken is not None:
            payload["verifyToken"] = verifyToken
        return self._request("PUT", f"/auth/profile/{user_id}", json=payload)

    def get_auth_user(self) -> dict[str, Any]:
        return self._request("GET", "/auth/user/me")

    def refresh_token(self, refreshToken: str) -> dict[str, Any]:
        return self._request(
            "POST", "/auth/refresh-token", json={"refreshToken": refreshToken}
        )

    # /--------- Video endpoints ---------/
    def analyze_video(self, url: str) -> dict[str, Any]:
        return self._request("POST", "/videos/analyze", json={"youtubeUrl": url})

    def video_status(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/videos/status/{job_id}")

    def get_analyzed_video(self, video_uid: str) -> dict[str, Any]:
        return self._request("GET", f"/videos/{video_uid}")

    def list_analyzed_videos(self) -> list[dict[str, Any]]:
        """Return the authenticated user's video library when the API exposes it."""
        return self.as_list(self._request("GET", "/videos"), "videos", "items", "results")

    # /--------- Chat endpoints ---------/

    def create_session(self, video_uid: str, title: str | None = None) -> dict[str, Any]:
        payload = {"title": title} if title else {}
        return self._request(
            "POST", f"/chat/sessions/{video_uid}", json=payload
        )

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.as_list(self._request("GET", "/chat/sessions"), "sessions", "items", "results")

    def stream_chat(self, session_id: str, question: str) -> Iterator[tuple[str, str]]:
        """Yield (event, payload) from the API's Server-Sent Events response."""
        try:
            response = requests.post(
                f"{self.endpoint}/chat/stream/{session_id}",
                headers={**self._headers(), "Accept": "text/event-stream"},
                json={"question": question},
                stream=True,
                timeout=(self.timeout, 120),
            )
        except requests.RequestException as exc:
            raise APIError(f"Could not start chat stream: {exc}") from exc
        if not response.ok:
            raise APIError(self._message(response), response.status_code)

        event, data = "message", []
        try:
            for raw in response.iter_lines(decode_unicode=True):
                line = raw or ""
                if not line:
                    if data:
                        yield event, "\n".join(data)
                    event, data = "message", []
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip())
            if data:
                yield event, "\n".join(data)
        except requests.RequestException as exc:
            raise APIError(f"Chat stream interrupted: {exc}") from exc
        finally:
            response.close()

    def list_chat_messages(self, session_id: str) -> list[dict[str, Any]]:
        return self.as_list(
            self._request("GET", f"/chat/sessions/{session_id}"),
            "messages", "items", "results",
        )

    def delete_chat_session(self, session_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/chat/sessions/{session_id}")


def extract_token(payload: dict[str, Any]) -> str | None:
    return (
        payload.get("accessToken")
        or payload.get("access_token")
        or (payload.get("tokens") or {}).get("accessToken")
    )


def extract_refresh_token(payload: dict[str, Any]) -> str | None:
    return (
        payload.get("refreshToken")
        or payload.get("refresh_token")
        or (payload.get("tokens") or {}).get("refreshToken")
    )


def extract_user(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("user") or payload.get("profile") or {}


def event_text(payload: str) -> str:
    """Read either a simple SSE string or JSON token payload."""
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return str(
                data.get("token") or data.get("content") or data.get("message") or ""
            )
    except json.JSONDecodeError:
        pass
    return payload
