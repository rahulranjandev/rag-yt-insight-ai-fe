from __future__ import annotations

import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
from api_client import APIError
from auth import client, is_authenticated, store_auth, sync_authenticated_user
from components.ui import apply_theme, sidebar
from pages import dashboard, video_chat

st.set_page_config(
    page_title="RAG Video Insight",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


def auth_screen() -> None:
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        st.markdown(
            "<br><div class='eyebrow'>RAG VIDEO INSIGHT</div><h1>Ask more of every video.</h1><p class='muted'>Analyze YouTube and Instagram videos, then chat with evidence-backed context.</p>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            mode = st.radio(
                "Authentication mode",
                ["Sign in", "Create account"],
                horizontal=True,
                label_visibility="collapsed",
            )
            with st.form("auth_form"):
                name = st.text_input("Name") if mode == "Create account" else ""
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(mode, use_container_width=True)
            if submitted:
                if not email or not password or (mode == "Create account" and not name):
                    st.warning("Complete all required fields to continue.")
                    return
                try:
                    result = (
                        client().register(name, email, password)
                        if mode == "Create account"
                        else client().login(email, password)
                    )
                    if store_auth(result):
                        sync_authenticated_user()
                        st.rerun()
                    else:
                        st.error(
                            "Authentication succeeded but no access token was returned. Check the API response mapping."
                        )
                except APIError as error:
                    st.error(str(error))


if not is_authenticated():
    auth_screen()
else:
    if not st.session_state.get("user"):
        sync_authenticated_user()
    if not is_authenticated():
        st.rerun()
    if "requested_page" in st.session_state:
        st.session_state.current_page = st.session_state.pop("requested_page")
    page = sidebar()
    if page == "Video chat":
        video_chat.render()
    else:
        dashboard.render()
