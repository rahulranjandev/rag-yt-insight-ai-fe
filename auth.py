"""Authentication state helpers kept separate from presentation."""

from __future__ import annotations

from typing import Any
import streamlit as st

from api_client import APIClient, APIError, extract_refresh_token, extract_token, extract_user


def client() -> APIClient:
    return APIClient(token=st.session_state.get("access_token"))


def is_authenticated() -> bool:
    return bool(st.session_state.get("access_token"))


def store_auth(payload: dict[str, Any]) -> bool:
    token = extract_token(payload)
    if not token:
        return False
    st.session_state.access_token = token
    user = extract_user(payload)
    if user:
        st.session_state.user = user
    refresh_token = extract_refresh_token(payload)
    if refresh_token:
        st.session_state.refresh_token = refresh_token
    return True


def sync_authenticated_user() -> None:
    """Hydrate sidebar identity from the protected user endpoint when possible."""
    try:
        user = client().get_auth_user()
    except APIError as first_error:
        try:
            user = client().get_user_profile()
        except APIError as second_error:
            if first_error.status_code == 401 or second_error.status_code == 401:
                logout()
            return
    if isinstance(user, dict):
        st.session_state.user = user.get("user") or user.get("profile") or user


def logout() -> None:
    for key in (
        "access_token",
        "refresh_token",
        "user",
        "selected_video",
        "job_id",
        "chat_session_id",
        "chat_history",
    ):
        st.session_state.pop(key, None)


def handle_api_error(error: APIError) -> None:
    if error.status_code == 401:
        refresh_token = st.session_state.get("refresh_token")
        if refresh_token:
            try:
                if store_auth(client().refresh_token(refresh_token)):
                    st.rerun()
            except APIError:
                pass
        logout()
        st.error("Your session expired. Please sign in again.")
        st.rerun()
    st.error(str(error))
