from __future__ import annotations

from html import escape
import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """<style>
      .stApp { background: radial-gradient(circle at 15% 0%, #25234c 0, #0b1020 40%, #080c18 100%); color: #edf0ff; }
      [data-testid="stSidebar"] { background: #0d1327; border-right: 1px solid rgba(255,255,255,.08); }
      .glass-card { background: rgba(22, 29, 56, .78); border: 1px solid rgba(168, 139, 250, .20); border-radius: 16px; padding: 1.25rem; box-shadow: 0 12px 35px rgba(0,0,0,.18); }
      .metric-card { background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.08); border-radius: 13px; padding: .9rem 1rem; min-height: 86px; }
      .metric-value { font-size: 1.45rem; font-weight: 750; color: #f5f3ff; } .metric-label { color: #aeb8d5; font-size: .82rem; }
      .eyebrow { color: #a78bfa; font-size: .78rem; font-weight: 700; letter-spacing: .10em; text-transform: uppercase; }
      .muted { color: #aeb8d5; }
      .status-ready { color: #86efac; font-weight: 700; } .status-failed { color: #fda4af; font-weight: 700; }
      div.stButton > button { border-radius: 9px; border: 0; background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; font-weight: 650; }
      [data-testid="stChatMessage"] { background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.06); border-radius: 12px; }
      [data-testid="stToolbar"] { visibility: hidden; } #MainMenu { visibility: hidden; } footer { visibility: hidden; }
    </style>""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, hint: str | None = None) -> None:
    hint_markup = f'<div class="muted">{escape(hint)}</div>' if hint else ""
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{escape(value)}</div><div class="metric-label">{escape(label)}</div>{hint_markup}</div>',
        unsafe_allow_html=True,
    )


def source_caption(sources: list[str]) -> None:
    if sources:
        st.caption("Sources: " + " · ".join(sources))


def status_card(status: str | None, detail: str | None = None) -> None:
    state = (status or "pending").lower()
    if state in {"completed", "complete", "ready", "success", "processed"}:
        label, klass = "Ready for questions", "status-ready"
    elif state in {"failed", "error"}:
        label, klass = "Processing failed", "status-failed"
    else:
        label, klass = "Processing video…", "muted"
    description = escape(
        str(detail or "We are fetching the video and grounding its transcript.")
    )
    st.markdown(
        f'<div class="glass-card"><div class="eyebrow">Analysis status</div><div class="{klass}">{label}</div><div class="muted">{description}</div></div>',
        unsafe_allow_html=True,
    )


def sidebar() -> str:
    user = st.session_state.get("user", {})
    with st.sidebar:
        st.markdown("## ✦ RAG Video Insight")
        st.caption("Grounded video intelligence")
        st.divider()
        st.markdown(
            f"**{escape(str(user.get('name') or user.get('email') or 'Signed in'))}**",
            unsafe_allow_html=True,
        )
        user_id = user.get("id") or user.get("userId") or user.get("uid")
        if user_id:
            with st.expander("Account"):
                with st.form("profile_form"):
                    name = st.text_input("Name", value=str(user.get("name") or ""))
                    email = st.text_input("Email", value=str(user.get("email") or ""))
                    save = st.form_submit_button("Save profile", use_container_width=True)
                if save:
                    from api_client import APIError
                    from auth import client
                    try:
                        updated = client().update_user_profile(str(user_id), name=name, email=email)
                        st.session_state.user = updated.get("user") or updated.get("profile") or updated
                        st.success("Profile updated.")
                    except APIError as error:
                        st.error(str(error))
        page = st.radio(
            "Workspace",
            ["Dashboard", "Video chat"],
            key="current_page",
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Log out", use_container_width=True):
            from auth import logout

            logout()
            st.rerun()
    return page
